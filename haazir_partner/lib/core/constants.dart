import 'package:flutter/foundation.dart';

class AppConstants {
  static String get defaultBaseUrl {
    const configured = String.fromEnvironment('HAAZIR_API_URL');
    if (configured.isEmpty) {
      if (kReleaseMode) {
        throw StateError(
          'Release build requires --dart-define=HAAZIR_API_URL=https://…/api/v1',
        );
      }
      return 'http://127.0.0.1:8000/api/v1';
    }
    final normalized = configured.replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !uri.hasScheme ||
        uri.host.isEmpty ||
        (kReleaseMode && uri.scheme != 'https')) {
      throw StateError(
        'HAAZIR_API_URL must be a valid${kReleaseMode ? ' HTTPS' : ''} API URL',
      );
    }
    return normalized;
  }

  static const String appName = 'Haazir Partner';
  static const String appTagline = 'Partner Operations Portal';
}
