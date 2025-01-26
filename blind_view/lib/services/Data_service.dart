import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class DataService {
  final String baseUrl;
  Timer? _timer;
  final StreamController<Map<String, dynamic>> _dataStreamController = StreamController.broadcast();

  DataService({required this.baseUrl});

  /// Exposes a stream to listen for data updates
  Stream<Map<String, dynamic>> get dataStream => _dataStreamController.stream;

  /// Starts fetching data every 10 seconds
  void startService() {
    _fetchData(); // Fetch data immediately

    // Start periodic fetching
    _timer = Timer.periodic(Duration(seconds: 10), (timer) {
      _fetchData();
    });
  }

  /// Stops the periodic fetching
  void stopService() {
    _timer?.cancel();
    _timer = null;
    _dataStreamController.close();
  }

  /// Fetch data from the API
  Future<void> _fetchData() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/data'));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _dataStreamController.add(data); // Add data to the stream
      } else {
        print('Error: ${response.statusCode} ${response.reasonPhrase}');
      }
    } catch (e) {
      print('Exception occurred: $e');
    }
  }
}
