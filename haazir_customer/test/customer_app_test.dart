import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:haazir_customer/core/theme.dart';
import 'package:haazir_customer/core/api_response.dart';
import 'package:haazir_customer/models/models.dart';
import 'package:haazir_customer/screens/login_screen.dart';
import 'package:http/http.dart' as http;

void main() {
  test('Plain-text server failure becomes a safe customer message', () {
    final response = http.Response(
      'Internal Server Error',
      500,
      headers: {'content-type': 'text/plain; charset=utf-8'},
    );

    expect(
      () => decodeApiResponse(response, successStatuses: const {200}),
      throwsA(
        isA<ApiException>().having(
          (error) => error.message,
          'message',
          'Something went wrong on our side. Please try again.',
        ),
      ),
    );
  });

  test('FastAPI validation details are mapped without exposing types', () {
    final response = http.Response(
      '{"detail":[{"msg":"Phone number is invalid"}]}',
      422,
      headers: {'content-type': 'application/json'},
    );

    expect(
      () => decodeApiResponse(response, successStatuses: const {200}),
      throwsA(
        isA<ApiException>().having(
          (error) => error.message,
          'message',
          'Phone number is invalid',
        ),
      ),
    );
  });

  test('Models serialization unit test', () {
    final user = User.fromJson({
      'id': 'u1',
      'phone': '+919876543210',
      'full_name': 'Test User',
      'role': 'CUSTOMER',
      'is_active': true,
      'is_suspended': false,
    });
    expect(user.id, 'u1');
    expect(user.phone, '+919876543210');
    expect(user.role, 'CUSTOMER');

    final quote = PriceQuote.fromJson({
      'id': 'q1',
      'service_id': 's1',
      'customer_id': 'u1',
      'base_charge': 200.0,
      'service_fee': 30.0,
      'emergency_surcharge': 0.0,
      'tax_amount': 11.5,
      'discount_amount': 0.0,
      'total_amount': 241.5,
      'currency': 'INR',
      'is_emergency': false,
      'expires_at': '2026-09-04T12:00:00Z',
    });
    expect(quote.totalAmount, 241.5);
    expect(quote.baseCharge, 200.0);

    final booking = Booking.fromJson({
      'id': 'b1',
      'booking_number': 'HZ-20260904-1234',
      'customer_id': 'u1',
      'service_id': 's1',
      'quote_id': 'q1',
      'status': 'REQUESTED',
      'address_snapshot': {'city': 'Bengaluru'},
      'service_snapshot': {'name': 'Tap Leak Repair'},
      'created_at': '2026-09-04T05:00:00Z',
    });
    expect(booking.status, 'REQUESTED');
    expect(booking.isTerminal, false);
  });

  testWidgets(
    'Customer Login screen renders phone, password and action buttons',
    (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(theme: HaazirTheme.lightTheme, home: const LoginScreen()),
      );

      expect(find.text('HAAZIR'), findsOneWidget);
      expect(find.text('Welcome back'), findsOneWidget);
      expect(find.text('Phone Number'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.widgetWithText(ElevatedButton, 'Continue'), findsOneWidget);
      for (final field in tester.widgetList<EditableText>(
        find.byType(EditableText),
      )) {
        expect(field.controller.text, isEmpty);
      }
    },
  );
}
