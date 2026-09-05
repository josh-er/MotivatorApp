import SwiftUI

struct ReturningUserView: View {
    @StateObject private var vm = SettingsLinkViewModel()
    var onBack: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: 24) {
            if let onBack {
                HStack {
                    Button(action: onBack) {
                        Label("Back", systemImage: "chevron.left")
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.accentGreenText)
                    Spacer()
                }
            }

            Image("AppLogo")
                .resizable()
                .scaledToFit()
                .frame(height: 60)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.top, 24)

            Text("Welcome back")
                .font(.title)
                .bold()
                .foregroundColor(.textPrimary)

            TextField("Phone number", text: $vm.phone)
                .foregroundColor(.textPrimary)
                .inputBordered()
                .keyboardType(.phonePad)

            Button("Get settings link") {
                vm.requestSettingsLink()
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(!vm.canRequestSettingsLink)

            if vm.isLoading {
                ProgressView()
            }

            Text(vm.message)
                .font(.footnote)
                .foregroundColor(vm.isError ? .errorText : .textSecondary)
                .padding(vm.isError ? 8 : 0)
                .background(vm.isError ? Color.errorBackground : Color.clear)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(vm.isError ? Color.errorBorder : Color.clear, lineWidth: 1)
                )

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.appBackground.ignoresSafeArea())
    }
}

#Preview {
    ReturningUserView()
}
