class AppConstants {
  static const String defaultBaseUrl = String.fromEnvironment(
    'HAAZIR_API_URL',
    defaultValue: 'https://api.haazir.invalid/api/v1',
  );
  static const String appName = 'Haazir Partner';
  static const String appTagline = 'Partner Operations Portal';
}
