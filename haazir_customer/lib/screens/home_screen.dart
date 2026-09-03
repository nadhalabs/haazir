import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'booking_request_screen.dart';
import 'bookings_history_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  List<ServiceCategory> _categories = [];
  List<ServiceItem> _popularServices = [];
  List<ServiceItem> _allServices = [];
  List<ServiceItem> _filteredServices = [];
  final _searchController = TextEditingController();

  bool _isLoading = true;
  String? _errorMessage;
  final String _currentCity = 'Choose a genuine service address at checkout';

  @override
  void initState() {
    super.initState();
    _loadHomeData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadHomeData() async {
    setState(() => _isLoading = true);
    try {
      final categories = await ApiService().getCategories();
      final services = await ApiService().getServices();

      if (mounted) {
        setState(() {
          _categories = categories;
          _allServices = services;
          _filteredServices = services;
          _popularServices = services.take(6).toList();
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

  void _onSearch(String query) {
    if (query.trim().isEmpty) {
      setState(() => _filteredServices = _allServices);
      return;
    }
    final q = query.toLowerCase();
    setState(() {
      _filteredServices = _allServices
          .where(
            (s) =>
                s.name.toLowerCase().contains(q) ||
                (s.description?.toLowerCase().contains(q) ?? false),
          )
          .toList();
    });
  }

  void _onSelectService(ServiceItem service, {bool isEmergency = false}) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            BookingRequestScreen(service: service, isEmergency: isEmergency),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildHomeFeed(),
          const BookingsHistoryScreen(),
          const ProfileScreen(),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: HaazirTheme.border, width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          selectedItemColor: HaazirTheme.primary,
          unselectedItemColor: HaazirTheme.textMuted,
          backgroundColor: Colors.white,
          elevation: 0,
          type: BottomNavigationBarType.fixed,
          onTap: (index) => setState(() => _currentIndex = index),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_filled),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.calendar_today_rounded),
              label: 'Bookings',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline_rounded),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHomeFeed() {
    return SafeArea(
      child: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: HaazirTheme.primary),
            )
          : RefreshIndicator(
              onRefresh: _loadHomeData,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 16,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: HaazirTheme.urgentRed.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.error_outline,
                              color: HaazirTheme.urgentRed,
                              size: 20,
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
                    // 1. Top Location Bar
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on_rounded,
                          color: HaazirTheme.primary,
                          size: 22,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Text(
                                    'Home',
                                    style: TextStyle(
                                      fontWeight: FontWeight.w800,
                                      fontSize: 15,
                                      color: HaazirTheme.textPrimary,
                                    ),
                                  ),
                                  Icon(
                                    Icons.keyboard_arrow_down_rounded,
                                    size: 20,
                                  ),
                                ],
                              ),
                              Text(
                                _currentCity,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: HaazirTheme.textSecondary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                        // Quick support / verified badge
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: HaazirTheme.primary.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Row(
                            children: [
                              Icon(
                                Icons.verified_rounded,
                                size: 14,
                                color: HaazirTheme.primary,
                              ),
                              SizedBox(width: 4),
                              Text(
                                'Verified',
                                style: TextStyle(
                                  color: HaazirTheme.primary,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // 2. Search Bar
                    TextField(
                      controller: _searchController,
                      onChanged: _onSearch,
                      decoration: InputDecoration(
                        hintText: 'What do you need help with? (e.g. tap, ac)',
                        prefixIcon: const Icon(
                          Icons.search_rounded,
                          color: HaazirTheme.textMuted,
                        ),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear_rounded, size: 18),
                                onPressed: () {
                                  _searchController.clear();
                                  _onSearch('');
                                },
                              )
                            : null,
                      ),
                    ),
                    const SizedBox(height: 24),

                    // If user is searching, show filtered services directly
                    if (_searchController.text.isNotEmpty) ...[
                      Text(
                        'Search Results (${_filteredServices.length})',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ..._filteredServices.map((s) => _buildServiceListTile(s)),
                    ] else ...[
                      // 3. Urgent / Need Someone Now Emergency Entry Banner
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF2F2), // Light Red
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFFCA5A5)),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: const BoxDecoration(
                                color: HaazirTheme.urgentRed,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.bolt_rounded,
                                color: Colors.white,
                                size: 22,
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Emergency or Urgent Need?',
                                    style: TextStyle(
                                      color: HaazirTheme.urgentRed,
                                      fontWeight: FontWeight.w800,
                                      fontSize: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    'Pipe burst, power outage, lockout? Get a pro dispatched in minutes.',
                                    style: TextStyle(
                                      color: Colors.red.shade900,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              style: TextButton.styleFrom(
                                foregroundColor: HaazirTheme.urgentRed,
                                textStyle: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 13,
                                ),
                              ),
                              onPressed: () {
                                if (_allServices.isNotEmpty) {
                                  _onSelectService(
                                    _allServices.first,
                                    isEmergency: true,
                                  );
                                }
                              },
                              child: const Text('Get Now'),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 28),

                      // 4. Service Categories Grid
                      const Text(
                        'Explore Services',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: HaazirTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 14),

                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 3,
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              childAspectRatio: 0.95,
                            ),
                        itemCount: _categories.length,
                        itemBuilder: (context, index) {
                          final cat = _categories[index];
                          return _buildCategoryCard(cat);
                        },
                      ),
                      const SizedBox(height: 32),

                      // 5. Popular Services Cards
                      const Text(
                        'Popular Right Now',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: HaazirTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 14),

                      ..._popularServices.map((s) => _buildServiceListTile(s)),
                    ],
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildCategoryCard(ServiceCategory cat) {
    IconData icon = Icons.handyman_rounded;
    Color iconColor = HaazirTheme.primary;

    if (cat.slug.contains('plumb')) {
      icon = Icons.water_drop_rounded;
    } else if (cat.slug.contains('elect')) {
      icon = Icons.flash_on_rounded;
    } else if (cat.slug.contains('appliance')) {
      icon = Icons.ac_unit_rounded;
    } else if (cat.slug.contains('mechanic')) {
      icon = Icons.directions_car_rounded;
    } else if (cat.slug.contains('locksmith')) {
      icon = Icons.lock_open_rounded;
    } else if (cat.slug.contains('carpenter')) {
      icon = Icons.chair_rounded;
    } else if (cat.slug.contains('clean')) {
      icon = Icons.cleaning_services_rounded;
    }

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          // Filter by category
          final matching = _allServices
              .where((s) => s.categoryId == cat.id)
              .toList();
          if (matching.isNotEmpty) {
            _onSelectService(matching.first);
          }
        },
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: iconColor, size: 24),
              ),
              const SizedBox(height: 10),
              Text(
                cat.name,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: HaazirTheme.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildServiceListTile(ServiceItem s) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _onSelectService(s),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: HaazirTheme.primary.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.build_rounded,
                    color: HaazirTheme.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        s.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: HaazirTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Starts from ₹${s.baseVisitCharge.toStringAsFixed(0)} • ~${s.estimatedDurationMins} mins',
                        style: const TextStyle(
                          fontSize: 12,
                          color: HaazirTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: HaazirTheme.primary,
                    minimumSize: const Size(70, 36),
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  onPressed: () => _onSelectService(s),
                  child: const Text(
                    'Book',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
