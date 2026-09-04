import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.diagnostic});

  final String message;
  final int? statusCode;
  final String? diagnostic;

  @override
  String toString() => message;
}

Future<http.Response> apiRequest(Future<http.Response> request) async {
  try {
    return await request.timeout(const Duration(seconds: 20));
  } on SocketException catch (error) {
    debugPrint('Haazir API network error: $error');
    throw const ApiException(
      'You’re offline. Check your internet connection and try again.',
    );
  } on http.ClientException catch (error) {
    debugPrint('Haazir API client error: $error');
    throw const ApiException(
      'We couldn’t connect to Haazir. Check your internet and try again.',
    );
  } on TimeoutException catch (error) {
    debugPrint('Haazir API timeout: $error');
    throw const ApiException(
      'Haazir is taking longer than expected. Please try again.',
    );
  }
}

dynamic decodeApiResponse(
  http.Response response, {
  required Set<int> successStatuses,
}) {
  final contentType = response.headers['content-type']?.toLowerCase() ?? '';
  final body = response.body.trim();
  dynamic decoded;

  if (body.isNotEmpty && contentType.contains('json')) {
    try {
      decoded = jsonDecode(body);
    } on FormatException catch (error) {
      debugPrint(
        'Haazir API invalid JSON (${response.statusCode}, $contentType): $error',
      );
    }
  }

  if (!successStatuses.contains(response.statusCode)) {
    final backendMessage = _extractDetail(decoded);
    final safeMessage = _messageForStatus(response.statusCode, backendMessage);
    debugPrint(
      'Haazir API error ${response.statusCode} ($contentType): '
      '${body.length > 500 ? body.substring(0, 500) : body}',
    );
    throw ApiException(
      safeMessage,
      statusCode: response.statusCode,
      diagnostic: backendMessage,
    );
  }

  if (body.isEmpty) {
    return null;
  }
  if (decoded == null) {
    debugPrint(
      'Haazir API expected JSON but received $contentType '
      '(${response.statusCode}).',
    );
    throw const ApiException(
      'Something went wrong while reading the server response. Please try again.',
    );
  }
  return decoded;
}

String? _extractDetail(dynamic decoded) {
  if (decoded is! Map) {
    return null;
  }
  final detail = decoded['detail'];
  if (detail is String && detail.trim().isNotEmpty) {
    return detail.trim();
  }
  if (detail is List) {
    final messages = detail
        .map((item) {
          if (item is Map && item['msg'] is String) {
            return item['msg'] as String;
          }
          return null;
        })
        .whereType<String>()
        .toList();
    if (messages.isNotEmpty) {
      return messages.join(' ');
    }
  }
  final message = decoded['message'];
  return message is String && message.trim().isNotEmpty ? message.trim() : null;
}

String _messageForStatus(int status, String? detail) {
  if (status == 401) {
    return 'Your session has expired. Please sign in again.';
  }
  if (status == 403) {
    return detail ?? 'This action isn’t available for your account.';
  }
  if (status == 404) {
    return detail ?? 'We couldn’t find what you requested.';
  }
  if (status == 409) {
    return detail ?? 'This request has already changed. Refresh and try again.';
  }
  if (status == 422) {
    return detail ?? 'Please check the information you entered.';
  }
  if (status == 429) {
    return 'Too many attempts. Please try again shortly.';
  }
  if (status >= 500) {
    return 'Something went wrong on our side. Please try again.';
  }
  return detail ?? 'Something went wrong. Please try again.';
}
