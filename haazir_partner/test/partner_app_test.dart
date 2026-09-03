import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:haazir_partner/core/theme.dart';
import 'package:haazir_partner/models/models.dart';
import 'package:haazir_partner/screens/login_screen.dart';

void main() {
  test('Partner models serialization unit test', () {
    final stats = DashboardStats.fromJson({
      'is_online': true,
      'is_available': true,
      'rating_average': 4.9,
      'rating_count': 22,
      'total_completed_jobs': 45,
      'today_completed_jobs': 3,
      'today_net_earnings': 850.0,
      'today_gross_earnings': 1000.0,
      'active_booking_id': 'b1',
      'active_booking_status': 'ASSIGNED',
    });

    expect(stats.isOnline, true);
    expect(stats.todayCompletedJobs, 3);
    expect(stats.todayNetEarnings, 850.0);
    expect(stats.activeBookingId, 'b1');

    final offer = IncomingOffer.fromJson({
      'assignment_id': 'a1',
      'booking_id': 'b1',
      'booking_number': 'HZ-20260904-9999',
      'service_name': 'AC Servicing',
      'customer_notes': 'Filter cleaning needed',
      'area': 'Bengaluru, Karnataka',
      'address_line1': '100 MG Road',
      'distance_km': 3.2,
      'estimated_duration_minutes': 20,
      'total_amount': 499.0,
      'estimated_net_earning': 424.15,
      'created_at': '2026-09-04T05:00:00Z',
    });

    expect(offer.bookingNumber, 'HZ-20260904-9999');
    expect(offer.estimatedNetEarning, 424.15);
    expect(offer.distanceKm, 3.2);
  });

  testWidgets(
    'Partner Login screen renders brand header, phone and submit action',
    (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PartnerTheme.lightTheme,
          home: const PartnerLoginScreen(),
        ),
      );

      expect(find.text('HAAZIR PARTNER'), findsOneWidget);
      expect(find.text('Partner Sign In'), findsOneWidget);
      expect(find.text('Registered Phone Number'), findsOneWidget);
      expect(
        find.widgetWithText(ElevatedButton, 'Enter Dashboard'),
        findsOneWidget,
      );
    },
  );
}
