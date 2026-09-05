import SwiftUI

struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(isEnabled ? Color.accentGreen : Color.disabledBackground)
            .foregroundColor(isEnabled ? .white : .disabledText)
            .cornerRadius(10)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
    }
}
