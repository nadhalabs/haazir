import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'live_booking_screen.dart';

class BookingRequestScreen extends StatefulWidget {
  final ServiceItem service;
  final bool isEmergency;

  const BookingRequestScreen({
    super.key,
    required this.service,
    this.isEmergency = false,
  });

  @override
  State<BookingRequestScreen> createState() => _BookingRequestScreenState();
}

class _BookingRequestScreenState extends State<BookingRequestScreen> {
  final _notesController = TextEditingController();
  List<Address> _addresses = [];
  Address? _selectedAddress;
  PriceQuote? _quote;

  bool _isLoading = true;
  bool _isRequesting = false;
  bool _isEmergency = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _isEmergency = widget.isEmergency;
    _loadData();
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final addresses = await ApiService().getAddresses();
      if (addresses.isEmpty) {
        // Create default address if none exists
        final newAddr = await ApiService().createAddress(
          label: 'Home',
          addressLine1: 'Flat 402, Green Glen Layout, Bellandur',
          city: 'Bengaluru',
          state: 'Karnataka',
          postalCode: '560103',
          latitude: 12.9279,
          longitude: 77.6771,
          isDefault: true,
        );
        _addresses = [newAddr];
      } else {
        _addresses = addresses;
      }
      _selectedAddress = _addresses.firstWhere(
        (a) => a.isDefault,
        orElse: () => _addresses.first,
      );

      // Fetch server authoritative quote
      await _fetchQuote();
    } catch (e) {
      setState(
        () => _errorMessage = e.toString().replaceAll('Exception: ', ''),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _fetchQuote() async {
    try {
      final quote = await ApiService().getQuote(
        serviceId: widget.service.id,
        isEmergency: _isEmergency,
      );
      if (mounted) {
        setState(() => _quote = quote);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = 'Failed to fetch price quote: $e');
      }
    }
  }

  Future<void> _confirmAndBook() async {
    if (_quote == null || _selectedAddress == null) return;

    setState(() {
      _isRequesting = true;
      _errorMessage = null;
    });

    try {
      final booking = await ApiService().createBooking(
        serviceId: widget.service.id,
        quoteId: _quote!.id,
        addressId: _selectedAddress!.id,
        customerNotes: _notesController.text.trim().isEmpty
            ? null
            : _notesController.text.trim(),
      );

      // Automatically trigger dispatch
      await ApiService().dispatchBooking(booking.id);

      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => LiveBookingScreen(bookingId: booking.id),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
          _isRequesting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Confirm Booking')),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: HaazirTheme.primary),
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
                        color: HaazirTheme.urgentRed.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: HaazirTheme.urgentRed.withValues(alpha: 0.2),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.error_outline,
                            color: HaazirTheme.urgentRed,
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

                  // Service Overview Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              color: HaazirTheme.primary.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: const Icon(
                              Icons.build_rounded,
                              color: HaazirTheme.primary,
                              size: 28,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  widget.service.name,
                                  style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.w700,
                                    color: HaazirTheme.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Est. ${widget.service.estimatedDurationMins} mins duration',
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
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Service Location Card
                  const Text(
                    'Service Location',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(
                            Icons.location_on_rounded,
                            color: HaazirTheme.primary,
                            size: 24,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _selectedAddress?.label ?? 'Address',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 14,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  _selectedAddress?.addressLine1 ?? '',
                                  style: const TextStyle(
                                    color: HaazirTheme.textSecondary,
                                    fontSize: 13,
                                  ),
                                ),
                                Text(
                                  '${_selectedAddress?.city}, ${_selectedAddress?.postalCode}',
                                  style: const TextStyle(
                                    color: HaazirTheme.textSecondary,
                                    fontSize: 13,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Emergency Toggle
                  Card(
                    child: SwitchListTile(
                      value: _isEmergency,
                      activeTrackColor: HaazirTheme.urgentRed.withValues(
                        alpha: 0.5,
                      ),
                      activeThumbColor: HaazirTheme.urgentRed,
                      title: const Text(
                        'Urgent / Emergency Service',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                      subtitle: const Text(
                        'Priority instant matching with nearby available technicians.',
                        style: TextStyle(
                          fontSize: 12,
                          color: HaazirTheme.textSecondary,
                        ),
                      ),
                      onChanged: (val) {
                        setState(() => _isEmergency = val);
                        _fetchQuote();
                      },
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Problem Description Field
                  const Text(
                    'Describe the issue',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _notesController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      hintText:
                          'e.g. Tap in the main kitchen sink is dripping continuously...',
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Authoritative Bill Breakdown
                  const Text(
                    'Price Breakdown',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  if (_quote != null) ...[
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            _billRow(
                              'Visit & Inspection Charge',
                              '₹${_quote!.baseCharge.toStringAsFixed(0)}',
                            ),
                            const SizedBox(height: 8),
                            _billRow(
                              'Platform Convenience Fee',
                              '₹${_quote!.serviceFee.toStringAsFixed(0)}',
                            ),
                            if (_quote!.isEmergency) ...[
                              const SizedBox(height: 8),
                              _billRow(
                                'Emergency Priority Surcharge',
                                '₹${_quote!.emergencySurcharge.toStringAsFixed(0)}',
                                isSurcharge: true,
                              ),
                            ],
                            const SizedBox(height: 8),
                            _billRow(
                              'Taxes & Levies',
                              '₹${_quote!.taxAmount.toStringAsFixed(2)}',
                            ),
                            const Divider(height: 24),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Total Payable',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w800,
                                    color: HaazirTheme.textPrimary,
                                  ),
                                ),
                                Text(
                                  '₹${_quote!.totalAmount.toStringAsFixed(2)}',
                                  style: const TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.w900,
                                    color: HaazirTheme.primary,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 32),

                  // Confirm and Request Button
                  ElevatedButton(
                    onPressed: _isRequesting ? null : _confirmAndBook,
                    child: _isRequesting
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            'Request Service • ₹${_quote?.totalAmount.toStringAsFixed(0) ?? ""}',
                          ),
                  ),
                  const SizedBox(height: 12),
                  const Center(
                    child: Text(
                      'Pay cash or UPI directly upon job completion',
                      style: TextStyle(
                        fontSize: 12,
                        color: HaazirTheme.textMuted,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }

  Widget _billRow(String title, String amount, {bool isSurcharge = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 13,
            color: isSurcharge
                ? HaazirTheme.urgentRed
                : HaazirTheme.textSecondary,
            fontWeight: isSurcharge ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
        Text(
          amount,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: isSurcharge
                ? HaazirTheme.urgentRed
                : HaazirTheme.textPrimary,
          ),
        ),
      ],
    );
  }
}
