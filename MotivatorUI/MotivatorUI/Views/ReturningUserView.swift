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
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(vm.isError ? 8 : 0)
                    .background(vm.isError ? Color.errorBackground : Color.clear)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(vm.isError ? Color.errorBorder : Color.clear, lineWidth: 1)
                    )

                Divider()

                VStack(spacing: 8) {
                    Text("To stop receiving messages, reply STOP to any text from us.")
                        .font(.footnote)
                        .foregroundColor(.textSecondary)

                    Link("Request data deletion", destination: dataDeletionURL)
                        .font(.footnote)
                        .foregroundColor(.accentGreenText)
                }

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

    private var dataDeletionURL: URL {
        var components = URLComponents()
        components.scheme = "mailto"
        components.path = "motivatorapphelp@gmail.com"
        components.queryItems = [
            URLQueryItem(name: "subject", value: "Data Deletion Request"),
            URLQueryItem(name: "body", value: "Please delete my data. My phone number is: \(vm.phone.isEmpty ? "[enter your phone number here]" : vm.phone)")
        ]
        return components.url ?? URL(string: "mailto:motivatorapphelp@gmail.com")!
    }
}

#Preview {
    ReturningUserView()
}
