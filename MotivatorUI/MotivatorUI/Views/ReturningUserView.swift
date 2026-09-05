import SwiftUI

struct ReturningUserView: View {
    @StateObject private var vm = SettingsLinkViewModel()
    var onBack: (() -> Void)? = nil

    var body: some View {
        ZStack(alignment: .topLeading) {
            VStack(spacing: 24) {
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
                    .tint(.textPrimary)
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

            if let onBack {
                Button(action: onBack) {
                    Label("Back", systemImage: "chevron.left")
                }
                .buttonStyle(.plain)
                .foregroundColor(.accentGreenText)
                .padding()
            }
        }
    }
}

#Preview {
    ReturningUserView()
}
