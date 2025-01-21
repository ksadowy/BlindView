import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatGPTService {
  final String _apiKey;
  DateTime? _lastRequestTime;
  final Duration _requestCooldown = const Duration(seconds: 2);

  ChatGPTService(this._apiKey);

  /// Sends a message to ChatGPT and returns its response.
  Future<String> sendMessageToChatGPT(String userMessage) async {
    const String apiUrl = 'https://api.openai.com/v1/chat/completions';

    final headers = _buildHeaders();
    final body = _buildRequestBody(userMessage);

    try {
      // Ensure minimum delay between requests
      await _applyRequestCooldown();

      // Sending POST request
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: headers,
        body: jsonEncode(body),
      );

      return _handleResponse(response);
    } catch (e) {
      return 'Error: $e';
    }
  }

  /// Builds the headers for the API request.
  Map<String, String> _buildHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $_apiKey',
    };
  }

  /// Builds the request body for the API call.
  Map<String, dynamic> _buildRequestBody(String userMessage) {
    return {
      'model': 'gpt-4o-mini-2024-07-18',
      'messages': [
        {
          'role': 'system',
          'content': "You are a helpful assistant for blind person. You have to answer in English."
        },
        {'role': 'user', 'content': userMessage},
      ],
    };
  }

  /// Handles the API response and extracts the reply.
  String _handleResponse(http.Response response) {
    if (response.statusCode == 200) {
      final Map<String, dynamic> responseData = jsonDecode(response.body);
      return responseData['choices'][0]['message']['content'] ?? 'No response content';
    } else {
      throw Exception('Failed to fetch response: ${response.statusCode} - ${response.body}');
    }
  }

  /// Ensures a cooldown period between requests.
  Future<void> _applyRequestCooldown() async {
    if (_lastRequestTime != null) {
      final timeSinceLastRequest = DateTime.now().difference(_lastRequestTime!);
      if (timeSinceLastRequest < _requestCooldown) {
        await Future.delayed(_requestCooldown - timeSinceLastRequest);
      }
    }
    _lastRequestTime = DateTime.now();
  }
}
