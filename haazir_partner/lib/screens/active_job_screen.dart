import 'dart:async';
import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class ActiveJobScreen extends StatefulWidget {
  final String bookingId;

  const ActiveJobScreen({super.key, required this.bookingId});

  @override
  State<ActiveJobScreen> createState() => _ActiveJobScreenState();
}

class _ActiveJobScreenState extends State<ActiveJobScreen> {
  PartnerBooking? _booking;
  Timer? _pollTimer;
  bool _isLoading = true;
  bool _isActionInProgress = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchJob();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchJob());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchJob() async {
    try {
      final b = await PartnerApiService().getBooking(widget.bookingId);
      if (mounted) {
        setState(() {
          _booking = b;
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

  Future<void> _transitionJob(String nextStatus) async {
    setState(() => _isActionInProgress = true);
    try {
      final updated = await PartnerApiService().updateBookingStatus(
        bookingId: widget.bookingId,
        toStatus: nextStatus,
      );
      if (mounted) {
        setState(() => _booking = updated);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Job status updated: ${nextStatus.replaceAll('_', ' ')}',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update status: $e'),
            backgroundColor: PartnerTheme.offlineRed,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isActionInProgress = false);
    }
  }

  Future<void> _collectCashPayment() async {
    final payment = _booking?.payment;
    if (payment == null || payment['id'] == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No active payment record found')),
      );
      return;
    }

    setState(() => _isActionInProgress = true);
    try {
      await PartnerApiService().collectCashPayment(payment['id']);
      await _fetchJob();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Payment confirmed! Earnings credited to wallet.'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Payment confirmation error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isActionInProgress = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: PartnerTheme.accent),
        ),
      );
    }

    final status = _booking?.status ?? 'ASSIGNED';
    final addr = _booking?.addressSnapshot ?? {};
    final serviceName = _booking?.serviceSnapshot['name'] ?? 'Service';

    return Scaffold(
      appBar: AppBar(
        title: Text('Job #${_booking?.bookingNumber ?? ""}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _fetchJob,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: PartnerTheme.offlineRed.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: PartnerTheme.offlineRed,
                      size: 20,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(
                          color: PartnerTheme.offlineRed,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Current Step Header
            _buildStatusHeader(status),
            const SizedBox(height: 20),

            // Customer & Location Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Customer Location',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                          ),
                        ),
                        Icon(
                          Icons.directions_rounded,
                          color: PartnerTheme.accent,
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    Text(
                      addr['address_line1'] ?? 'Location Address',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${addr['city'] ?? ""}, ${addr['state'] ?? ""} ${addr['postal_code'] ?? ""}',
                      style: const TextStyle(
                        color: PartnerTheme.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                    if (_booking?.customerNotes != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: PartnerTheme.background,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(
                              Icons.notes_rounded,
                              size: 16,
                              color: PartnerTheme.textMuted,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Note: ${_booking!.customerNotes!}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Payout Card
            Card(
              color: PartnerTheme.accent.withValues(alpha: 0.05),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Your Net Payout for this Job',
                          style: TextStyle(
                            fontSize: 12,
                            color: PartnerTheme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '₹${_booking?.providerEarning.toStringAsFixed(2) ?? "0.00"}',
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                            color: PartnerTheme.accent,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: PartnerTheme.accent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        serviceName,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                          color: PartnerTheme.accent,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Action Button Depending on Current State
            _buildActionSection(status),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusHeader(String status) {
    Color color = PartnerTheme.accent;
    String label = 'Job Assigned';

    switch (status) {
      case 'ASSIGNED':
        label = '1. Job Assigned • Tap Start Travel';
        color = PartnerTheme.accent;
        break;
      case 'PROVIDER_EN_ROUTE':
        label = '2. Travelling to Customer Location';
        color = PartnerTheme.busyAmber;
        break;
      case 'ARRIVED':
        label = '3. Arrived at Doorstep';
        color = PartnerTheme.accent;
        break;
      case 'IN_PROGRESS':
        label = '4. Work in Progress';
        color = PartnerTheme.primary;
        break;
      case 'COMPLETED':
        label = '5. Job Completed';
        color = PartnerTheme.onlineGreen;
        break;
      case 'CANCELLED':
        label = 'Job Cancelled';
        color = PartnerTheme.offlineRed;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.flag_circle_rounded, color: color, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w800,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionSection(String status) {
    if (_isActionInProgress) {
      return const Center(
        child: CircularProgressIndicator(color: PartnerTheme.accent),
      );
    }

    switch (status) {
      case 'ASSIGNED':
        return ElevatedButton.icon(
          onPressed: () => _transitionJob('PROVIDER_EN_ROUTE'),
          icon: const Icon(Icons.navigation_rounded),
          label: const Text('START TRAVEL (EN ROUTE)'),
        );
      case 'PROVIDER_EN_ROUTE':
        return ElevatedButton.icon(
          onPressed: () => _transitionJob('ARRIVED'),
          style: ElevatedButton.styleFrom(
            backgroundColor: PartnerTheme.busyAmber,
          ),
          icon: const Icon(Icons.door_front_door_rounded),
          label: const Text("I'VE ARRIVED AT LOCATION"),
        );
      case 'ARRIVED':
        return ElevatedButton.icon(
          onPressed: () => _transitionJob('IN_PROGRESS'),
          style: ElevatedButton.styleFrom(backgroundColor: PartnerTheme.accent),
          icon: const Icon(Icons.handyman_rounded),
          label: const Text('START WORK'),
        );
      case 'IN_PROGRESS':
        return ElevatedButton.icon(
          onPressed: () => _transitionJob('COMPLETED'),
          style: ElevatedButton.styleFrom(
            backgroundColor: PartnerTheme.onlineGreen,
          ),
          icon: const Icon(Icons.check_circle_rounded),
          label: const Text('COMPLETE JOB'),
        );
      case 'COMPLETED':
        final payment = _booking?.payment;
        final bool isPaid = payment != null && payment['status'] == 'PAID';

        return Column(
          children: [
            if (!isPaid) ...[
              ElevatedButton.icon(
                onPressed: _collectCashPayment,
                style: ElevatedButton.styleFrom(
                  backgroundColor: PartnerTheme.onlineGreen,
                ),
                icon: const Icon(Icons.payments_rounded),
                label: const Text('COLLECT CASH & CONFIRM PAYMENT'),
              ),
              const SizedBox(height: 12),
            ],
            OutlinedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('RETURN TO DASHBOARD'),
            ),
          ],
        );
      default:
        return OutlinedButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('BACK TO DASHBOARD'),
        );
    }
  }
}
