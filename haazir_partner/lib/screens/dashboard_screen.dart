import 'dart:async';
import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'active_job_screen.dart';
import 'login_screen.dart';

class PartnerDashboardScreen extends StatefulWidget {
  const PartnerDashboardScreen({super.key});

  @override
  State<PartnerDashboardScreen> createState() => _PartnerDashboardScreenState();
}

class _PartnerDashboardScreenState extends State<PartnerDashboardScreen> {
  DashboardStats? _stats;
  List<IncomingOffer> _offers = [];
  Timer? _refreshTimer;
  Timer? _locationTimer;

  bool _isLoading = true;
  bool _isOnline = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
    // Poll for new incoming dispatch offers every 3 seconds
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _pollOffersAndStats(),
    );
    // Send live provider location heartbeat every 20 seconds while online
    _locationTimer = Timer.periodic(
      const Duration(seconds: 20),
      (_) => _sendHeartbeatIfOnline(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _locationTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadDashboard() async {
    setState(() => _isLoading = true);
    try {
      final stats = await PartnerApiService().getDashboardStats();
      final offers = await PartnerApiService().getIncomingOffers();
      if (mounted) {
        setState(() {
          _stats = stats;
          _isOnline = stats.isOnline;
          _offers = offers;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _pollOffersAndStats() async {
    try {
      final offers = await PartnerApiService().getIncomingOffers();
      final stats = await PartnerApiService().getDashboardStats();
      if (mounted) {
        setState(() {
          _offers = offers;
          _stats = stats;
        });
      }
    } catch (_) {}
  }

  Future<void> _sendHeartbeatIfOnline() async {
    if (!_isOnline) return;
    try {
      // Simulate live device GPS coordinates for provider
      await PartnerApiService().sendLocationHeartbeat(
        latitude: 12.9716,
        longitude: 77.5946,
        presenceStatus: 'ONLINE_AVAILABLE',
      );
    } catch (_) {}
  }

  Future<void> _toggleOnlineStatus(bool value) async {
    setState(() => _isOnline = value);
    try {
      await PartnerApiService().updatePresence(
        isOnline: value,
        isAvailable: value,
      );
      if (value) {
        await _sendHeartbeatIfOnline();
      }
      _loadDashboard();
    } catch (e) {
      if (mounted) {
        setState(() => _isOnline = !value);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to change status: $e')));
      }
    }
  }

  Future<void> _acceptOffer(IncomingOffer offer) async {
    try {
      final job = await PartnerApiService().acceptBooking(offer.bookingId);
      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => ActiveJobScreen(bookingId: job.id)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not accept: $e'),
            backgroundColor: PartnerTheme.offlineRed,
          ),
        );
      }
      _loadDashboard();
    }
  }

  Future<void> _rejectOffer(IncomingOffer offer) async {
    try {
      await PartnerApiService().rejectBooking(offer.bookingId);
      _pollOffersAndStats();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Could not reject: $e')));
      }
    }
  }

  Future<void> _logout() async {
    await PartnerApiService().logout();
    if (mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const PartnerLoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Haazir Partner'),
        actions: [
          IconButton(
            icon: const Icon(
              Icons.logout_rounded,
              color: PartnerTheme.textSecondary,
            ),
            onPressed: _logout,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: PartnerTheme.accent),
            )
          : SingleChildScrollView(
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
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(
                          color: PartnerTheme.offlineRed,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // 1. Online / Offline Hero Toggle
                  _buildDutyToggleCard(),
                  const SizedBox(height: 20),

                  // 2. Active Job Banner if any
                  if (_stats?.activeBookingId != null) ...[
                    _buildActiveJobBanner(),
                    const SizedBox(height: 20),
                  ],

                  // 3. Incoming Dispatch Request Cards
                  if (_offers.isNotEmpty) ...[
                    const Row(
                      children: [
                        Icon(
                          Icons.bolt_rounded,
                          color: PartnerTheme.busyAmber,
                          size: 22,
                        ),
                        SizedBox(width: 6),
                        Text(
                          'Incoming Service Requests',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: PartnerTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ..._offers.map((offer) => _buildIncomingOfferCard(offer)),
                    const SizedBox(height: 20),
                  ],

                  // 4. Performance & Today Earnings Card
                  const Text(
                    'Today Overview',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 12),
                  _buildEarningsSummary(),
                  const SizedBox(height: 24),

                  // 5. Verification Status Card
                  _buildVerificationCard(),
                ],
              ),
            ),
    );
  }

  Widget _buildDutyToggleCard() {
    final statusColor = _isOnline
        ? PartnerTheme.onlineGreen
        : PartnerTheme.offlineRed;
    return Card(
      color: statusColor.withValues(alpha: 0.08),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: statusColor.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _isOnline
                    ? Icons.power_settings_new_rounded
                    : Icons.pause_circle_outline_rounded,
                color: statusColor,
                size: 28,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _isOnline ? 'ONLINE & READY' : 'OFFLINE',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                      color: statusColor,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _isOnline
                        ? 'Broadcasting live location to nearby jobs'
                        : 'Go online to receive incoming requests',
                    style: const TextStyle(
                      fontSize: 12,
                      color: PartnerTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            Switch(
              value: _isOnline,
              activeTrackColor: PartnerTheme.onlineGreen.withValues(alpha: 0.5),
              activeThumbColor: PartnerTheme.onlineGreen,
              onChanged: _toggleOnlineStatus,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveJobBanner() {
    return Card(
      color: PartnerTheme.accent.withValues(alpha: 0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(
              Icons.engineering_rounded,
              color: PartnerTheme.accent,
              size: 28,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Active Job in Progress',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Status: ${_stats?.activeBookingStatus?.replaceAll("_", " ") ?? ""}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: PartnerTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(90, 38),
                padding: const EdgeInsets.symmetric(horizontal: 12),
              ),
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        ActiveJobScreen(bookingId: _stats!.activeBookingId!),
                  ),
                );
              },
              child: const Text(
                'Open Job',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIncomingOfferCard(IncomingOffer offer) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Card(
        color: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: PartnerTheme.busyAmber, width: 2),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: PartnerTheme.busyAmber.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      offer.serviceName,
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: PartnerTheme.busyAmber,
                      ),
                    ),
                  ),
                  Text(
                    '${offer.distanceKm} km away',
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: PartnerTheme.textSecondary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                offer.area,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: PartnerTheme.textPrimary,
                ),
              ),
              Text(
                offer.addressLine1,
                style: const TextStyle(
                  fontSize: 13,
                  color: PartnerTheme.textSecondary,
                ),
              ),
              if (offer.customerNotes != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Notes: ${offer.customerNotes}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                    color: PartnerTheme.textSecondary,
                  ),
                ),
              ],
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'You Earn (Est.)',
                        style: TextStyle(
                          fontSize: 11,
                          color: PartnerTheme.textMuted,
                        ),
                      ),
                      Text(
                        '₹${offer.estimatedNetEarning.toStringAsFixed(0)}',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                          color: PartnerTheme.onlineGreen,
                        ),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(80, 44),
                          side: const BorderSide(color: PartnerTheme.border),
                        ),
                        onPressed: () => _rejectOffer(offer),
                        child: const Text('Decline'),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: PartnerTheme.accent,
                          minimumSize: const Size(110, 44),
                        ),
                        onPressed: () => _acceptOffer(offer),
                        child: const Text('Accept Job'),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEarningsSummary() {
    return Row(
      children: [
        Expanded(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Today's Net Earnings",
                    style: TextStyle(
                      fontSize: 12,
                      color: PartnerTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '₹${_stats?.todayNetEarnings.toStringAsFixed(0) ?? "0"}',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      color: PartnerTheme.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Jobs Completed',
                    style: TextStyle(
                      fontSize: 12,
                      color: PartnerTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${_stats?.todayCompletedJobs ?? 0}',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      color: PartnerTheme.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildVerificationCard() {
    return Card(
      child: ListTile(
        leading: const Icon(
          Icons.shield_rounded,
          color: PartnerTheme.accent,
          size: 28,
        ),
        title: const Text(
          'Partner Verification',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
        ),
        subtitle: const Text(
          'Admin Verified • Active V1 Service Professional',
          style: TextStyle(fontSize: 12, color: PartnerTheme.textSecondary),
        ),
        trailing: const Icon(
          Icons.check_circle_rounded,
          color: PartnerTheme.onlineGreen,
        ),
      ),
    );
  }
}
