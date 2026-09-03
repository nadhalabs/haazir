import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  User? _user;
  List<Address> _addresses = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _isLoading = true);
    try {
      final user = await ApiService().getProfile();
      final addrs = await ApiService().getAddresses();
      if (mounted) {
        setState(() {
          _user = user;
          _addresses = addrs;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _logout() async {
    await ApiService().logout();
    if (mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Profile')),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: HaazirTheme.primary),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  // User Avatar & Name
                  Center(
                    child: Column(
                      children: [
                        CircleAvatar(
                          radius: 40,
                          backgroundColor: HaazirTheme.primary.withValues(
                            alpha: 0.1,
                          ),
                          child: const Icon(
                            Icons.person_rounded,
                            size: 48,
                            color: HaazirTheme.primary,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _user?.fullName ?? 'User Profile',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _user?.phone ?? '',
                          style: const TextStyle(
                            fontSize: 14,
                            color: HaazirTheme.textSecondary,
                          ),
                        ),
                        if (_user?.email != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            _user!.email!,
                            style: const TextStyle(
                              fontSize: 13,
                              color: HaazirTheme.textMuted,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Saved Addresses Card
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
                                'Saved Addresses',
                                style: TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 15,
                                ),
                              ),
                              Icon(
                                Icons.add_location_alt_outlined,
                                color: HaazirTheme.primary,
                                size: 20,
                              ),
                            ],
                          ),
                          const Divider(height: 20),
                          if (_addresses.isEmpty)
                            const Text(
                              'No saved addresses yet.',
                              style: TextStyle(
                                color: HaazirTheme.textSecondary,
                                fontSize: 13,
                              ),
                            )
                          else
                            ..._addresses.map(
                              (a) => Padding(
                                padding: const EdgeInsets.only(bottom: 12),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(
                                      Icons.location_on_outlined,
                                      size: 20,
                                      color: HaazirTheme.primary,
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            a.label,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w600,
                                              fontSize: 14,
                                            ),
                                          ),
                                          Text(
                                            a.formattedSummary,
                                            style: const TextStyle(
                                              fontSize: 12,
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
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Support & Help
                  Card(
                    child: Column(
                      children: [
                        ListTile(
                          leading: const Icon(
                            Icons.support_agent_rounded,
                            color: HaazirTheme.primary,
                          ),
                          title: const Text(
                            'Haazir Customer Support',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'Support helpline: 1800-HAAZIR-HELP (24x7)',
                                ),
                              ),
                            );
                          },
                        ),
                        const Divider(height: 1),
                        ListTile(
                          leading: const Icon(
                            Icons.verified_user_outlined,
                            color: HaazirTheme.primary,
                          ),
                          title: const Text(
                            'Trust & Verified Guarantee',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: () {},
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Logout Button
                  OutlinedButton.icon(
                    onPressed: _logout,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: HaazirTheme.urgentRed,
                      side: const BorderSide(color: HaazirTheme.urgentRed),
                    ),
                    icon: const Icon(Icons.logout_rounded, size: 18),
                    label: const Text('Log Out'),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Haazir Version 1.0.0 (Production Build)',
                    style: TextStyle(
                      fontSize: 11,
                      color: HaazirTheme.textMuted,
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
