import SwiftUI

private struct InputBorderModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.inputBorder, lineWidth: 1)
            )
    }
}

extension View {
    func inputBordered() -> some View {
        modifier(InputBorderModifier())
    }
}
