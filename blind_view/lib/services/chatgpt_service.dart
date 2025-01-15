import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatGPTService {
  String _apiKey = "your_api_key_here";
  DateTime? _lastRequestTime;
  final Duration _requestCooldown = Duration(seconds: 2); // minimalne opóźnienie między zapytaniami

  ChatGPTService(this._apiKey);

  Future<String> sendMessageToChatGPT(String userMessage) async {

    const String apiUrl = 'https://api.openai.com/v1/chat/completions';

    // Headers for the API request
    Map<String, String> headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $_apiKey',
    };

    // Request body with model and messages
    Map<String, dynamic> body = {
      'model': 'gpt-4o-mini-2024-07-18',
      'messages': [{'role': 'system', 'content': "You are a helpful assistant for blind person. You have to answer in English."},
                   {'role': 'user', 'content': userMessage}]
    };

    try {
      // Sending POST request
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: headers,
        body: jsonEncode(body),
      );

      // Check if the request was successful
      if (response.statusCode == 200) {
        final Map<String, dynamic> responseData = jsonDecode(response.body);

        // Extracting the reply from the response
        String reply = responseData['choices'][0]['message']['content'];
        print(reply);
        return reply;
      } else {
        // Handle errors
        throw Exception('Failed to fetch response: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      // Handle exceptions
      return 'Error: $e';
    }
  }
}
