import Foundation

enum APIError: Error {
    case httpStatus(Int)
}

class APIClient {

    func postJSON(url: String, body: [String: Any], completion: @escaping (Result<Void, Error>) -> Void) {
        guard let url = URL(string: url) else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { _, response, error in
            if error != nil {
                completion(.failure(error!))
                return
            }

            if let httpResponse = response as? HTTPURLResponse, !(200...299).contains(httpResponse.statusCode) {
                completion(.failure(APIError.httpStatus(httpResponse.statusCode)))
                return
            }

            completion(.success(()))
        }.resume()
    }
}
