import Foundation

enum APIError: Error {
    case network(Error)
    case httpStatus(Int, String?)
}

class APIClient {

    func postJSON(url: String, body: [String: Any], completion: @escaping (Result<Void, Error>) -> Void) {
        guard let url = URL(string: url) else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(APIError.network(error)))
                return
            }

            if let httpResponse = response as? HTTPURLResponse, !(200...299).contains(httpResponse.statusCode) {
                let errorCode = data.flatMap { try? JSONDecoder().decode(ErrorResponse.self, from: $0) }?.error
                completion(.failure(APIError.httpStatus(httpResponse.statusCode, errorCode)))
                return
            }

            completion(.success(()))
        }.resume()
    }
}
