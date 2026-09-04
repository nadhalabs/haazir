import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/constants.dart';
import '../core/api_response.dart';
import '../models/models.dart';

class PartnerApiService {
  static final PartnerApiService _instance = PartnerApiService._internal();
  factory PartnerApiService() => _instance;
  PartnerApiService._internal();

  final String _baseUrl = AppConstants.defaultBaseUrl;
  String? _accessToken;
  ProviderUser? _currentUser;
  ProviderProfile? _currentProfile;
  static const _secureStorage = FlutterSecureStorage();

  String get baseUrl => _baseUrl;
  ProviderUser? get currentUser => _currentUser;
  ProviderProfile? get currentProfile => _currentProfile;
  bool get isAuthenticated => _accessToken != null;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = await _secureStorage.read(key: 'partner_access_token');
    final userJson = prefs.getString('partner_user');
    if (userJson != null) {
      try {
        _currentUser = ProviderUser.fromJson(jsonDecode(userJson));
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

  Future<http.Response> _patch(
    Uri uri, {
    required Map<String, String> headers,
    Object? body,
  }) => apiRequest(http.patch(uri, headers: headers, body: body));

  dynamic _decode(http.Response response) =>
      decodeApiResponse(response, successStatuses: const {200, 201, 204});

  Never _fail(http.Response response) {
    decodeApiResponse(response, successStatuses: const {});
    throw const ApiException('Something went wrong. Please try again.');
  }

  // --- AUTHENTICATION ---

  Future<ProviderUser> register({
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
        'role': 'PROVIDER',
      }),
    );

    if (res.statusCode == 201) {
      return await login(phone: phone, password: password);
    } else {
      _fail(res);
    }
  }

  Future<ProviderUser> login({
    required String phone,
    required String password,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/auth/login'),
      headers: _headers(requiresAuth: false),
      body: jsonEncode({'phone': phone, 'password': password}),
    );

    if (res.statusCode == 200) {
      final data = _decode(res);
      _accessToken = data['access_token'];
      final prefs = await SharedPreferences.getInstance();
      await _secureStorage.write(
        key: 'partner_access_token',
        value: _accessToken!,
      );

      final user = await getProfile();
      _currentUser = user;
      _currentProfile = await getProviderProfile();

      await prefs.setString(
        'partner_user',
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

  Future<ProviderUser> getProfile() async {
    final res = await _get(Uri.parse('$_baseUrl/auth/me'), headers: _headers());
    if (res.statusCode == 200) {
      return ProviderUser.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<ProviderProfile> getProviderProfile() async {
    final res = await _get(
      Uri.parse('$_baseUrl/providers/me'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return ProviderProfile.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<void> logout() async {
    // Mark offline before logging out
    try {
      await updatePresence(isOnline: false, isAvailable: false);
    } catch (_) {}
    _accessToken = null;
    _currentUser = null;
    _currentProfile = null;
    final prefs = await SharedPreferences.getInstance();
    await _secureStorage.delete(key: 'partner_access_token');
    await prefs.remove('partner_user');
  }

  // --- DASHBOARD & AVAILABILITY ---

  Future<DashboardStats> getDashboardStats() async {
    final res = await _get(
      Uri.parse('$_baseUrl/providers/me/dashboard-stats'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return DashboardStats.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<void> updatePresence({
    required bool isOnline,
    required bool isAvailable,
  }) async {
    final res = await _patch(
      Uri.parse('$_baseUrl/providers/me/status'),
      headers: _headers(),
      body: jsonEncode({'is_online': isOnline, 'is_available': isAvailable}),
    );
    if (res.statusCode != 200) {
      _fail(res);
    }
  }

  Future<void> sendLocationHeartbeat({
    required double latitude,
    required double longitude,
    required String presenceStatus,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/providers/me/location'),
      headers: _headers(),
      body: jsonEncode({
        'latitude': latitude,
        'longitude': longitude,
        'presence_status': presenceStatus,
      }),
    );
    _decode(res);
  }

  // --- OFFERS & ACTIVE JOBS ---

  Future<List<IncomingOffer>> getIncomingOffers() async {
    final res = await _get(
      Uri.parse('$_baseUrl/providers/me/incoming-offers'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => IncomingOffer.fromJson(e)).toList();
    }
    _fail(res);
  }

  Future<PartnerBooking> acceptBooking(String bookingId) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings/$bookingId/accept'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return PartnerBooking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<void> rejectBooking(String bookingId) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings/$bookingId/reject'),
      headers: _headers(),
    );
    if (res.statusCode != 200) {
      _fail(res);
    }
  }

  Future<PartnerBooking> getBooking(String bookingId) async {
    final res = await _get(
      Uri.parse('$_baseUrl/bookings/$bookingId'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      return PartnerBooking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<PartnerBooking> updateBookingStatus({
    required String bookingId,
    required String toStatus,
    String? reason,
  }) async {
    final res = await _post(
      Uri.parse('$_baseUrl/bookings/$bookingId/status'),
      headers: _headers(),
      body: jsonEncode({'to_status': toStatus, 'reason': reason}),
    );
    if (res.statusCode == 200) {
      return PartnerBooking.fromJson(_decode(res));
    }
    _fail(res);
  }

  Future<void> collectCashPayment(String paymentId) async {
    final res = await _post(
      Uri.parse('$_baseUrl/payments/$paymentId/complete'),
      headers: _headers(),
      body: jsonEncode({}),
    );
    if (res.statusCode != 200) {
      _fail(res);
    }
  }

  Future<List<PartnerBooking>> getPartnerBookingHistory() async {
    final res = await _get(
      Uri.parse('$_baseUrl/bookings'),
      headers: _headers(),
    );
    if (res.statusCode == 200) {
      final List list = _decode(res);
      return list.map((e) => PartnerBooking.fromJson(e)).toList();
    }
    _fail(res);
  }
}
