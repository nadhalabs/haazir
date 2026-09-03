import 'dart:async';
import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class LiveBookingScreen extends StatefulWidget {
  final String bookingId;

  const LiveBookingScreen({super.key, required this.bookingId});

  @override
  State<LiveBookingScreen> createState() => _LiveBookingScreenState();
}

class _LiveBookingScreenState extends State<LiveBookingScreen> {
  Booking? _booking;
  Timer? _pollTimer;
  bool _isLoading = true;
  String? _errorMessage;

  // Rating input state for completion screen
  int _selectedRating = 5;
  final _reviewController = TextEditingController();
  bool _isSubmittingRating = false;
  bool _ratingSubmitted = false;

  @override
  void initState() {
    super.initState();
    _fetchBooking();
    // Safe polling fallback every 3 seconds
    _pollTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _fetchBooking(),
    );
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _reviewController.dispose();
    super.dispose();
  }

  Future<void> _fetchBooking() async {
    try {
      final booking = await ApiService().getBooking(widget.bookingId);
      if (mounted) {
        setState(() {
          _booking = booking;
          _isLoading = false;
          _errorMessage = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(
          () => _errorMessage = e.toString().replaceAll('Exception: ', ''),
        );
      }
    }
  }

  Future<void> _cancelBooking() async {
    final reasonController = TextEditingController();
    final shouldCancel = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancel Request?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Are you sure you want to cancel this booking?'),
            const SizedBox(height: 12),
            TextField(
              controller: reasonController,
              decoration: const InputDecoration(
                hintText: 'Reason for cancellation',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('No'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: HaazirTheme.urgentRed,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Yes, Cancel'),
          ),
        ],
      ),
    );

    if (shouldCancel == true) {
      try {
        await ApiService().cancelBooking(
          widget.bookingId,
          reasonController.text.trim().isEmpty
              ? 'Cancelled by customer'
              : reasonController.text.trim(),
        );
        _fetchBooking();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('Failed to cancel: $e')));
        }
      }
    }
  }

  Future<void> _submitRating() async {
    setState(() => _isSubmittingRating = true);
    try {
      await ApiService().submitRating(
        bookingId: widget.bookingId,
        score: _selectedRating,
        reviewText: _reviewController.text.trim().isEmpty
            ? null
            : _reviewController.text.trim(),
      );
      if (mounted) {
        setState(() => _ratingSubmitted = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Thank you for rating your service partner!'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Could not submit rating: $e')));
      }
    } finally {
      if (mounted) setState(() => _isSubmittingRating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: HaazirTheme.primary),
        ),
      );
    }

    final status = _booking?.status ?? 'REQUESTED';

    return Scaffold(
      appBar: AppBar(
        title: Text(_booking?.bookingNumber ?? 'Booking Details'),
        actions: [
          if (status == 'REQUESTED' ||
              status == 'SEARCHING' ||
              status == 'ASSIGNED')
            TextButton(
              onPressed: _cancelBooking,
              child: const Text(
                'Cancel',
                style: TextStyle(
                  color: HaazirTheme.urgentRed,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchBooking,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: HaazirTheme.urgentRed.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.error_outline,
                        color: HaazirTheme.urgentRed,
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(
                            color: HaazirTheme.urgentRed,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              // Hero Status Card
              _buildStatusHeader(status),
              const SizedBox(height: 24),

              // Provider Card if Assigned
              if (_booking?.providerSnapshot != null) ...[
                _buildProviderDetailsCard(),
                const SizedBox(height: 20),
              ],

              // Work & Price Breakdown Card
              _buildBookingDetailsCard(),
              const SizedBox(height: 20),

              // Completion / Rating Card
              if (status == 'COMPLETED') ...[
                _buildCompletionAndRatingCard(),
                const SizedBox(height: 20),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusHeader(String status) {
    String title = 'Searching for professional...';
    String subtitle = 'Broadcasting to verified providers near your location';
    IconData icon = Icons.radar_rounded;
    Color statusColor = HaazirTheme.primary;
    int stepIndex = 0;

    switch (status) {
      case 'REQUESTED':
      case 'SEARCHING':
        title = 'Finding your professional...';
        subtitle = 'Connecting you with the closest verified specialist';
        icon = Icons.search_rounded;
        stepIndex = 1;
        break;
      case 'ASSIGNED':
        title = 'Professional Confirmed!';
        subtitle = 'Your technician has accepted the job and is preparing';
        icon = Icons.check_circle_outline_rounded;
        stepIndex = 2;
        break;
      case 'PROVIDER_EN_ROUTE':
        title = 'Technician on the way';
        subtitle = 'Expected arrival in approx 10-15 mins';
        icon = Icons.directions_bike_rounded;
        stepIndex = 3;
        break;
      case 'ARRIVED':
        title = 'Technician Arrived';
        subtitle = 'Professional is at your doorstep';
        icon = Icons.home_repair_service_rounded;
        stepIndex = 4;
        break;
      case 'IN_PROGRESS':
        title = 'Work in Progress';
        subtitle = 'Service is actively being performed';
        icon = Icons.engineering_rounded;
        stepIndex = 5;
        break;
      case 'COMPLETED':
        title = 'Job Completed Successfully!';
        subtitle = 'Please verify work and pay the service partner';
        icon = Icons.verified_rounded;
        statusColor = HaazirTheme.success;
        stepIndex = 6;
        break;
      case 'CANCELLED':
        title = 'Booking Cancelled';
        subtitle =
            _booking?.cancellationReason ?? 'This request was cancelled.';
        icon = Icons.cancel_outlined;
        statusColor = HaazirTheme.urgentRed;
        stepIndex = 0;
        break;
    }

    return Card(
      color: statusColor.withValues(alpha: 0.06),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: statusColor, size: 28),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: statusColor,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 13,
                          color: HaazirTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (status != 'CANCELLED' && status != 'COMPLETED') ...[
              const SizedBox(height: 20),
              // Linear Progress Indicator
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: stepIndex / 6.0,
                  backgroundColor: HaazirTheme.border,
                  valueColor: AlwaysStoppedAnimation<Color>(statusColor),
                  minHeight: 6,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProviderDetailsCard() {
    final p = _booking!.providerSnapshot!;
    final name = p['business_name'] ?? 'Assigned Partner';
    final rating = (p['rating_average'] as num?)?.toDouble() ?? 4.9;
    final ratingCount = p['rating_count'] ?? 18;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: HaazirTheme.primary.withValues(alpha: 0.1),
              child: const Icon(
                Icons.person_rounded,
                color: HaazirTheme.primary,
                size: 32,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(
                        Icons.star_rounded,
                        color: Colors.amber,
                        size: 18,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '$rating ($ratingCount jobs)',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            IconButton.filled(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'Calling technician via masked marketplace proxy...',
                    ),
                  ),
                );
              },
              icon: const Icon(Icons.call_rounded),
              style: IconButton.styleFrom(backgroundColor: HaazirTheme.primary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBookingDetailsCard() {
    final serviceName = _booking?.serviceSnapshot['name'] ?? 'Service';
    final address = _booking?.addressSnapshot['address_line1'] ?? 'Location';
    final total = _booking?.priceQuote?.totalAmount ?? 0.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Booking Summary',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
            ),
            const Divider(height: 20),
            _infoRow(Icons.build_rounded, 'Service', serviceName),
            const SizedBox(height: 10),
            _infoRow(Icons.location_on_rounded, 'Address', address),
            const SizedBox(height: 10),
            _infoRow(
              Icons.payments_rounded,
              'Estimated Total',
              '₹${total.toStringAsFixed(2)}',
            ),
            if (_booking?.customerNotes != null) ...[
              const SizedBox(height: 10),
              _infoRow(
                Icons.notes_rounded,
                'Customer Notes',
                _booking!.customerNotes!,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: HaazirTheme.textMuted),
        const SizedBox(width: 10),
        SizedBox(
          width: 90,
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 13,
              color: HaazirTheme.textSecondary,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: HaazirTheme.textPrimary,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCompletionAndRatingCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Rate Service Experience',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            const Text(
              'Your rating helps maintain high quality standards on Haazir.',
              style: TextStyle(fontSize: 13, color: HaazirTheme.textSecondary),
            ),
            const SizedBox(height: 16),
            if (_ratingSubmitted || _booking?.rating != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: HaazirTheme.success.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  children: [
                    Icon(
                      Icons.check_circle_rounded,
                      color: HaazirTheme.success,
                    ),
                    SizedBox(width: 10),
                    Text(
                      'Rating submitted! Thank you.',
                      style: TextStyle(
                        color: HaazirTheme.success,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (index) {
                  final score = index + 1;
                  return IconButton(
                    iconSize: 36,
                    icon: Icon(
                      score <= _selectedRating
                          ? Icons.star_rounded
                          : Icons.star_border_rounded,
                      color: Colors.amber,
                    ),
                    onPressed: () => setState(() => _selectedRating = score),
                  );
                }),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _reviewController,
                decoration: const InputDecoration(
                  hintText: 'Share a few words about the technician work...',
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _isSubmittingRating ? null : _submitRating,
                child: _isSubmittingRating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text('Submit Review'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
