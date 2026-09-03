import 'package:flutter/material.dart';
import 'core/theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService().init();
  runApp(const HaazirCustomerApp());
}

class HaazirCustomerApp extends StatelessWidget {
  const HaazirCustomerApp({super.key});

  @override
  Widget build(BuildContext context) {
    final bool isLoggedIn = ApiService().isAuthenticated;

    return MaterialApp(
      title: 'Haazir Customer',
      debugShowCheckedModeBanner: false,
      theme: HaazirTheme.lightTheme,
      home: isLoggedIn ? const HomeScreen() : const LoginScreen(),
    );
  }
}
