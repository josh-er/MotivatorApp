import Foundation
import Combine

class DeliveryTimeViewModel: ObservableObject {
    @Published var selectedTime: Date = Date()

    var formattedLocalTime: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: selectedTime)
    }
}
