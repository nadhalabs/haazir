class User {
  final String id;
  final String phone;
  final String fullName;
  final String? email;
  final String role;
  final bool isActive;
  final bool isSuspended;

  User({
    required this.id,
    required this.phone,
    required this.fullName,
    this.email,
    required this.role,
    required this.isActive,
    required this.isSuspended,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? '',
      phone: json['phone'] ?? '',
      fullName: json['full_name'] ?? '',
      email: json['email'],
      role: json['role'] ?? 'CUSTOMER',
      isActive: json['is_active'] ?? true,
      isSuspended: json['is_suspended'] ?? false,
    );
  }
}

class Address {
  final String id;
  final String label;
  final String addressLine1;
  final String? addressLine2;
  final String city;
  final String state;
  final String postalCode;
  final double latitude;
  final double longitude;
  final bool isDefault;

  Address({
    required this.id,
    required this.label,
    required this.addressLine1,
    this.addressLine2,
    required this.city,
    required this.state,
    required this.postalCode,
    required this.latitude,
    required this.longitude,
    required this.isDefault,
  });

  factory Address.fromJson(Map<String, dynamic> json) {
    return Address(
      id: json['id'] ?? '',
      label: json['label'] ?? 'Home',
      addressLine1: json['address_line1'] ?? '',
      addressLine2: json['address_line2'],
      city: json['city'] ?? '',
      state: json['state'] ?? '',
      postalCode: json['postal_code'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0.0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0.0,
      isDefault: json['is_default'] ?? false,
    );
  }

  String get formattedSummary => '$addressLine1, $city';
}

class ServiceCategory {
  final String id;
  final String name;
  final String slug;
  final String? description;
  final String? iconUrl;
  final int displayOrder;

  ServiceCategory({
    required this.id,
    required this.name,
    required this.slug,
    this.description,
    this.iconUrl,
    required this.displayOrder,
  });

  factory ServiceCategory.fromJson(Map<String, dynamic> json) {
    return ServiceCategory(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      slug: json['slug'] ?? '',
      description: json['description'],
      iconUrl: json['icon_url'],
      displayOrder: json['display_order'] ?? 0,
    );
  }
}

class ServiceItem {
  final String id;
  final String categoryId;
  final String name;
  final String slug;
  final String? description;
  final int estimatedDurationMins;
  final double baseVisitCharge;
  final double? minCharge;
  final double emergencySurchargeRate;
  final bool isActive;

  ServiceItem({
    required this.id,
    required this.categoryId,
    required this.name,
    required this.slug,
    this.description,
    required this.estimatedDurationMins,
    required this.baseVisitCharge,
    this.minCharge,
    required this.emergencySurchargeRate,
    required this.isActive,
  });

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      id: json['id'] ?? '',
      categoryId: json['category_id'] ?? '',
      name: json['name'] ?? '',
      slug: json['slug'] ?? '',
      description: json['description'],
      estimatedDurationMins: json['estimated_duration_mins'] ?? 60,
      baseVisitCharge: (json['base_visit_charge'] as num?)?.toDouble() ?? 0.0,
      minCharge: (json['min_charge'] as num?)?.toDouble(),
      emergencySurchargeRate:
          (json['emergency_surcharge_rate'] as num?)?.toDouble() ?? 0.0,
      isActive: json['is_active'] ?? true,
    );
  }
}

class PriceQuote {
  final String id;
  final String serviceId;
  final String customerId;
  final double baseCharge;
  final double serviceFee;
  final double emergencySurcharge;
  final double taxAmount;
  final double discountAmount;
  final double totalAmount;
  final String currency;
  final bool isEmergency;
  final String expiresAt;

  PriceQuote({
    required this.id,
    required this.serviceId,
    required this.customerId,
    required this.baseCharge,
    required this.serviceFee,
    required this.emergencySurcharge,
    required this.taxAmount,
    required this.discountAmount,
    required this.totalAmount,
    required this.currency,
    required this.isEmergency,
    required this.expiresAt,
  });

  factory PriceQuote.fromJson(Map<String, dynamic> json) {
    return PriceQuote(
      id: json['id'] ?? '',
      serviceId: json['service_id'] ?? '',
      customerId: json['customer_id'] ?? '',
      baseCharge: (json['base_charge'] as num?)?.toDouble() ?? 0.0,
      serviceFee: (json['service_fee'] as num?)?.toDouble() ?? 0.0,
      emergencySurcharge:
          (json['emergency_surcharge'] as num?)?.toDouble() ?? 0.0,
      taxAmount: (json['tax_amount'] as num?)?.toDouble() ?? 0.0,
      discountAmount: (json['discount_amount'] as num?)?.toDouble() ?? 0.0,
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] ?? 'INR',
      isEmergency: json['is_emergency'] ?? false,
      expiresAt: json['expires_at'] ?? '',
    );
  }
}

class Booking {
  final String id;
  final String bookingNumber;
  final String customerId;
  final String? providerId;
  final String serviceId;
  final String quoteId;
  final String status;
  final String? customerNotes;
  final Map<String, dynamic> addressSnapshot;
  final Map<String, dynamic> serviceSnapshot;
  final Map<String, dynamic>? providerSnapshot;
  final String? scheduledFor;
  final String? startedAt;
  final String? completedAt;
  final String? cancelledAt;
  final String? cancellationReason;
  final String createdAt;
  final PriceQuote? priceQuote;
  final Map<String, dynamic>? payment;
  final Map<String, dynamic>? rating;

  Booking({
    required this.id,
    required this.bookingNumber,
    required this.customerId,
    this.providerId,
    required this.serviceId,
    required this.quoteId,
    required this.status,
    this.customerNotes,
    required this.addressSnapshot,
    required this.serviceSnapshot,
    this.providerSnapshot,
    this.scheduledFor,
    this.startedAt,
    this.completedAt,
    this.cancelledAt,
    this.cancellationReason,
    required this.createdAt,
    this.priceQuote,
    this.payment,
    this.rating,
  });

  factory Booking.fromJson(Map<String, dynamic> json) {
    return Booking(
      id: json['id'] ?? '',
      bookingNumber: json['booking_number'] ?? '',
      customerId: json['customer_id'] ?? '',
      providerId: json['provider_id'],
      serviceId: json['service_id'] ?? '',
      quoteId: json['quote_id'] ?? '',
      status: json['status'] ?? 'REQUESTED',
      customerNotes: json['customer_notes'],
      addressSnapshot: json['address_snapshot'] is Map
          ? Map<String, dynamic>.from(json['address_snapshot'])
          : {},
      serviceSnapshot: json['service_snapshot'] is Map
          ? Map<String, dynamic>.from(json['service_snapshot'])
          : {},
      providerSnapshot: json['provider_snapshot'] is Map
          ? Map<String, dynamic>.from(json['provider_snapshot'])
          : null,
      scheduledFor: json['scheduled_for'],
      startedAt: json['started_at'],
      completedAt: json['completed_at'],
      cancelledAt: json['cancelled_at'],
      cancellationReason: json['cancellation_reason'],
      createdAt: json['created_at'] ?? '',
      priceQuote: json['price_quote'] != null
          ? PriceQuote.fromJson(json['price_quote'])
          : null,
      payment: json['payment'] is Map
          ? Map<String, dynamic>.from(json['payment'])
          : null,
      rating: json['rating'] is Map
          ? Map<String, dynamic>.from(json['rating'])
          : null,
    );
  }

  bool get isTerminal =>
      status == 'COMPLETED' || status == 'CANCELLED' || status == 'FAILED';
}
