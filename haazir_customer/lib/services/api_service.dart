import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/constants.dart';
import '../core/api_response.dart';
import '../models/models.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final String _baseUrl = AppConstants.defaultBaseUrl;
  String? _accessToken;
  User? _currentUser;
  static const _secureStorage = FlutterSecureStorage();

  String get baseUrl => _baseUrl;
  User? get currentUser => _currentUser;
  bool get isAuthenticated => _accessToken != null;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = await _secureStorage.read(key: 'access_token');
    final userJson = prefs.getString('current_user');
    if (userJson != null) {
      try {
        _currentUser = User.fromJson(jsonDecode(userJson));
      } catch (_) {}
    }
  }

  Map<String, String> _headers({bool requiresAuth = true}) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (requiresAuth && _accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    return headers;
  }

  Future<http.Response> _get(Uri uri, {required Map<String, String> headers}) =>
      apiRequest(http.get(uri, headers: headers));

  Future<http.Response> _post(
    Uri uri, {
    required Map<String, String> headers,
    Object? body,
  }) => apiRequest(http.post(uri, headers: headers, body: body));

  dynamic _decode(http.Response response) =>
      decodeApiResponse(response, successStatuses: const {200, 201, 204});

  Never _fail(http.Response response) {
    decodeApiResponse(response, successStatuses: const {});
    throw const ApiException('Something went wrong. Please try again.');
  }

  // --- AUTHENTICATION ---

  Future<User> register({
    required String phone,
    required String password,
    required String fullName,
    String? email,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/auth/register'),
      headers: _headers(requiresAuth: false),
      body: jsonEncode({
        'phone': phone,
        'password': password,
        'full_name': fullName,
        'email': email,
        'role': 'CUSTOMER',
      }),
    );

    if (res.statusCode == 201) {
      // Auto login
      return await login(phone: phone, password: password);
    } else {
      _fail(res);
    }
  }

  Future<User> login({required String phone, required String password}) async {
    final res = await _post(
      Uri.parse('$_baseUrl/auth/login'),
      headers: _headers(requiresAuth: false),
      body: jsonEncode({'phone': phone, 'password': password}),
    );

    if (res.statusCode == 200) {
      final data = _decode(res);
      _accessToken = data['access_token'];
      final prefs = await SharedPreferences.getInstance();
      await _secureStorage.write(key: 'access_token', value: _accessToken!);

      // Fetch profile
      final user = await getProfile();
      _currentUser = user;
      await prefs.setString(
        'current_user',
        jsonEncode({
          'id': user.id,
          'phone': user.phone,
          'full_name': user.fullName,
          'email': user.email,
          'role': user.role,
          'is_active': user.isActive,
          'is_suspended': user.isSuspended,
        }),
      );
      return user;
    } else {
      _fail(res);
    }
  }

  Future<User> getProfile() async {
    final res = await _get(Uri.parse('$_baseUrl/auth/me'), headers: _headers());
    if (res.statusCode == 200) {
      return User.fromJson(_decode(res));
    } else {
      _fail(res);
    }
  }

  Future<void> logout() async {
    _accessToken = null;
    _currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await _secureStorage.delete(key: 'access_token');
    await prefs.remove('current_user');
  }

  // --- SERVICES & CATEGORIES ---

  Future<List<ServiceCategory>> getCategories() async {
    final res = await _get(
      Uri.parse('$_baseUrl/services/categories'),
      headers: _headers(requiresAuth: false),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => ServiceCategory.fromJson(e)).toList();
    }
    _fail(res);
  }

  Future<List<ServiceItem>> getServices({String? categoryId}) async {
    var url = '$_baseUrl/services';
    if (categoryId != null) {
      url += '?category_id=$categoryId';
    }
    final res = await _get(
      Uri.parse(url),
      headers: _headers(requiresAuth: false),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => ServiceItem.fromJson(e)).toList();
    }
    _fail(res);
  }

  // --- ADDRESSES ---

  Future<List<Address>> getAddresses() async {
    final res = await _get(
      Uri.parse('$_baseUrl/users/addresses'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => Address.fromJson(e)).toList();
    }
    _fail(res);
  }

  Future<Address> createAddress({
    required String label,
    required String addressLine1,
    String? addressLine2,
    required String city,
    required String state,
    required String postalCode,
    required double latitude,
    required double longitude,
    bool isDefault = true,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/users/addresses'),
      headers: _headers(),
      body: jsonEncode({
        'label': label,
        'address_line1': addressLine1,
        'address_line2': addressLine2,
        'city': city,
        'state': state,
        'postal_code': postalCode,
        'latitude': latitude,
        'longitude': longitude,
        'is_default': isDefault,
      }),
    );
    if (res.statusCode == 201) {
      return Address.fromJson(_decode(res));
    }
    _fail(res);
  }

  // --- PRICING QUOTE ---

  Future<PriceQuote> getQuote({
    required String serviceId,
    bool isEmergency = false,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/pricing/quote'),
      headers: _headers(),
      body: jsonEncode({'service_id': serviceId, 'is_emergency': isEmergency}),
    );
    if (res.statusCode == 200) {
      return PriceQuote.fromJson(_decode(res));
    }
    _fail(res);
  }

  // --- BOOKINGS ---

  Future<Booking> createBooking({
    required String serviceId,
    required String quoteId,
    required String addressId,
    String? customerNotes,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings'),
      headers: _headers(),
      body: jsonEncode({
        'service_id': serviceId,
        'quote_id': quoteId,
        'address_id': addressId,
        'customer_notes': customerNotes,
      }),
    );
    if (res.statusCode == 201) {
      return Booking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<Booking> dispatchBooking(String bookingId) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings/$bookingId/dispatch'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return Booking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<Booking> getBooking(String bookingId) async {
    final res = await _get(
      Uri.parse('$_baseUrl/bookings/$bookingId'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return Booking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<List<Booking>> getMyBookings() async {
    final res = await _get(
      Uri.parse('$_baseUrl/bookings'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => Booking.fromJson(e)).toList();
    }
    _fail(res);
  }

  Future<Booking> cancelBooking(String bookingId, String reason) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings/$bookingId/cancel'),
      headers: _headers(),
      body: jsonEncode({'cancellation_reason': reason}),
    );
    if (res.statusCode == 200) {
      return Booking.fromJson(_decode(res));
    }
    _fail(res);
  }

  // --- PAYMENTS & RATINGS ---

  Future<void> initiatePayment(String bookingId, String method) async {
    final res = await _post(
      Uri.parse('$_baseUrl/payments'),
      headers: _headers(),
      body: jsonEncode({'booking_id': bookingId, 'payment_method': method}),
    );
    if (res.statusCode != 201 && res.statusCode != 200) {
      _fail(res);
    }
  }

  Future<void> submitRating({
    required String bookingId,
    required int score,
    String? reviewText,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/ratings'),
      headers: _headers(),
      body: jsonEncode({
        'booking_id': bookingId,
        'score': score,
        'review_text': reviewText,
      }),
    );
    if (res.statusCode != 201) {
      _fail(res);
    }
  }
}
