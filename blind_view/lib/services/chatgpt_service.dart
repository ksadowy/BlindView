import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatGPTService {
  final String _apiKey;

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
      'model': 'gpt-3.5-turbo',
      'messages': [
        {'role': 'user', 'content': userMessage}
      ]
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
