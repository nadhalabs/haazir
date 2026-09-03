class AppConstants {
  static const String defaultBaseUrl = String.fromEnvironment(
    'HAAZIR_API_URL',
    defaultValue: 'https://api.haazir.invalid/api/v1',
  );
  static const String appName = 'Haazir';
  static const String appTagline = 'Instant Local Services at Your Doorstep';
}
