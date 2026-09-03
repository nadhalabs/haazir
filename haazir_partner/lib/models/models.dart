class ProviderUser {
  final String id;
  final String phone;
  final String fullName;
  final String? email;
  final String role;
  final bool isActive;
  final bool isSuspended;

  ProviderUser({
    required this.id,
    required this.phone,
    required this.fullName,
    this.email,
    required this.role,
    required this.isActive,
    required this.isSuspended,
  });

  factory ProviderUser.fromJson(Map<String, dynamic> json) {
    return ProviderUser(
      id: json['id'] ?? '',
      phone: json['phone'] ?? '',
      fullName: json['full_name'] ?? '',
      email: json['email'],
      role: json['role'] ?? 'PROVIDER',
      isActive: json['is_active'] ?? true,
      isSuspended: json['is_suspended'] ?? false,
    );
  }
}

class ProviderProfile {
  final String id;
  final String userId;
  final String? businessName;
  final String? bio;
  final String verificationStatus; // PENDING, VERIFIED, REJECTED
  final double serviceRadiusKm;
  final double? baseLatitude;
  final double? baseLongitude;
  final bool isOnline;
  final bool isAvailable;
  final double ratingAverage;
  final int ratingCount;
  final int completedJobsCount;

  ProviderProfile({
    required this.id,
    required this.userId,
    this.businessName,
    this.bio,
    required this.verificationStatus,
    required this.serviceRadiusKm,
    this.baseLatitude,
    this.baseLongitude,
    required this.isOnline,
    required this.isAvailable,
    required this.ratingAverage,
    required this.ratingCount,
    required this.completedJobsCount,
  });

  factory ProviderProfile.fromJson(Map<String, dynamic> json) {
    return ProviderProfile(
      id: json['id'] ?? '',
      userId: json['user_id'] ?? '',
      businessName: json['business_name'],
      bio: json['bio'],
      verificationStatus: json['verification_status'] ?? 'PENDING',
      serviceRadiusKm: (json['service_radius_km'] as num?)?.toDouble() ?? 15.0,
      baseLatitude: (json['base_latitude'] as num?)?.toDouble(),
      baseLongitude: (json['base_longitude'] as num?)?.toDouble(),
      isOnline: json['is_online'] ?? false,
      isAvailable: json['is_available'] ?? false,
      ratingAverage: (json['rating_average'] as num?)?.toDouble() ?? 0.0,
      ratingCount: json['rating_count'] ?? 0,
      completedJobsCount: json['completed_jobs_count'] ?? 0,
    );
  }
}

class IncomingOffer {
  final String assignmentId;
  final String bookingId;
  final String bookingNumber;
  final String serviceName;
  final String? customerNotes;
  final String area;
  final String addressLine1;
  final double distanceKm;
  final int estimatedDurationMinutes;
  final double totalAmount;
  final double estimatedNetEarning;
  final String createdAt;

  IncomingOffer({
    required this.assignmentId,
    required this.bookingId,
    required this.bookingNumber,
    required this.serviceName,
    this.customerNotes,
    required this.area,
    required this.addressLine1,
    required this.distanceKm,
    required this.estimatedDurationMinutes,
    required this.totalAmount,
    required this.estimatedNetEarning,
    required this.createdAt,
  });

  factory IncomingOffer.fromJson(Map<String, dynamic> json) {
    return IncomingOffer(
      assignmentId: json['assignment_id'] ?? '',
      bookingId: json['booking_id'] ?? '',
      bookingNumber: json['booking_number'] ?? '',
      serviceName: json['service_name'] ?? 'Service',
      customerNotes: json['customer_notes'],
      area: json['area'] ?? '',
      addressLine1: json['address_line1'] ?? '',
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0.0,
      estimatedDurationMinutes: json['estimated_duration_minutes'] ?? 15,
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0.0,
      estimatedNetEarning:
          (json['estimated_net_earning'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] ?? '',
    );
  }
}

class DashboardStats {
  final bool isOnline;
  final bool isAvailable;
  final double ratingAverage;
  final int ratingCount;
  final int totalCompletedJobs;
  final int todayCompletedJobs;
  final double todayNetEarnings;
  final double todayGrossEarnings;
  final String? activeBookingId;
  final String? activeBookingStatus;

  DashboardStats({
    required this.isOnline,
    required this.isAvailable,
    required this.ratingAverage,
    required this.ratingCount,
    required this.totalCompletedJobs,
    required this.todayCompletedJobs,
    required this.todayNetEarnings,
    required this.todayGrossEarnings,
    this.activeBookingId,
    this.activeBookingStatus,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      isOnline: json['is_online'] ?? false,
      isAvailable: json['is_available'] ?? false,
      ratingAverage: (json['rating_average'] as num?)?.toDouble() ?? 0.0,
      ratingCount: json['rating_count'] ?? 0,
      totalCompletedJobs: json['total_completed_jobs'] ?? 0,
      todayCompletedJobs: json['today_completed_jobs'] ?? 0,
      todayNetEarnings: (json['today_net_earnings'] as num?)?.toDouble() ?? 0.0,
      todayGrossEarnings:
          (json['today_gross_earnings'] as num?)?.toDouble() ?? 0.0,
      activeBookingId: json['active_booking_id'],
      activeBookingStatus: json['active_booking_status'],
    );
  }
}

class PartnerBooking {
  final String id;
  final String bookingNumber;
  final String status;
  final String? customerNotes;
  final Map<String, dynamic> addressSnapshot;
  final Map<String, dynamic> serviceSnapshot;
  final String createdAt;
  final double totalAmount;
  final double providerEarning;
  final Map<String, dynamic>? payment;

  PartnerBooking({
    required this.id,
    required this.bookingNumber,
    required this.status,
    this.customerNotes,
    required this.addressSnapshot,
    required this.serviceSnapshot,
    required this.createdAt,
    required this.totalAmount,
    required this.providerEarning,
    this.payment,
  });

  factory PartnerBooking.fromJson(Map<String, dynamic> json) {
    final quote = json['price_quote'] is Map ? json['price_quote'] : {};
    final earning = json['earning'] is Map ? json['earning'] : {};

    return PartnerBooking(
      id: json['id'] ?? '',
      bookingNumber: json['booking_number'] ?? '',
      status: json['status'] ?? 'ASSIGNED',
      customerNotes: json['customer_notes'],
      addressSnapshot: json['address_snapshot'] is Map
          ? Map<String, dynamic>.from(json['address_snapshot'])
          : {},
      serviceSnapshot: json['service_snapshot'] is Map
          ? Map<String, dynamic>.from(json['service_snapshot'])
          : {},
      createdAt: json['created_at'] ?? '',
      totalAmount: (quote['total_amount'] as num?)?.toDouble() ?? 0.0,
      providerEarning: (earning['provider_earning'] as num?)?.toDouble() ?? 0.0,
      payment: json['payment'] is Map
          ? Map<String, dynamic>.from(json['payment'])
          : null,
    );
  }
}
