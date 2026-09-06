import SwiftUI

private let supportedTimezones: [(id: String, label: String)] = [
    ("America/New_York",             "Eastern (New York)"),
    ("America/Chicago",              "Central (Chicago)"),
    ("America/Denver",               "Mountain (Denver)"),
    ("America/Phoenix",              "Mountain \u{2013} no DST (Phoenix)"),
    ("America/Los_Angeles",          "Pacific (Los Angeles)"),
    ("America/Anchorage",            "Alaska (Anchorage)"),
    ("America/Nome",                 "Alaska (Nome)"),
    ("America/Juneau",               "Alaska (Juneau)"),
    ("Pacific/Honolulu",             "Hawaii \u{2013} no DST (Honolulu)"),
    ("America/Adak",                 "Hawaii-Aleutian (Adak)"),
    ("America/Indiana/Indianapolis", "Eastern \u{2013} no DST (Indianapolis)"),
    ("America/Boise",                "Mountain (Boise)"),
]

struct PhoneEntryView: View {
    @StateObject var vm: PhoneEntryViewModel
    let onRequestReturningUser: () -> Void

    init(
        onSignUpSuccess: @escaping (String) -> Void = { _ in },
        onRequestReturningUser: @escaping () -> Void = {}
    ) {
        _vm = StateObject(wrappedValue: PhoneEntryViewModel(onSignUpSuccess: onSignUpSuccess))
        self.onRequestReturningUser = onRequestReturningUser
    }

    var body: some View {
        VStack(spacing: 24) {
            Image("AppLogo")
                .resizable()
                .scaledToFit()
                .frame(height: 60)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.top, 24)

            PhoneNumberField(vm: vm.phoneNumber)
            DeliveryTimePicker(vm: vm.deliveryTime)
            TimezonePicker(vm: vm.timezone)
            ConsentCheckboxRow(vm: vm.consent)

            SubmitButton(phoneNumber: vm.phoneNumber, consent: vm.consent, timezone: vm.timezone, action: vm.signUp)

            ReturningUserLinkButton(vm: vm.submissionStatus, action: onRequestReturningUser)

            SubmissionStatusView(vm: vm.submissionStatus, onRequestReturningUser: onRequestReturningUser)

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.appBackground.ignoresSafeArea())
    }
}

private struct PhoneNumberField: View {
    @ObservedObject var vm: PhoneNumberViewModel

    var body: some View {
        TextField("Phone number", text: $vm.phone)
            .foregroundColor(.textPrimary)
            .tint(.textPrimary)
            .inputBordered()
            .keyboardType(.phonePad)
    }
}

private struct DeliveryTimePicker: View {
    @ObservedObject var vm: DeliveryTimeViewModel

    var body: some View {
        DatePicker(
            "Select delivery time",
            selection: $vm.selectedTime,
            displayedComponents: .hourAndMinute
        )
        .foregroundColor(.textPrimary)
        .tint(.accentGreenText)
        .datePickerStyle(.compact)
        .inputBordered()
    }
}

private struct TimezonePicker: View {
    @ObservedObject var vm: TimezoneViewModel

    var body: some View {
        Picker(selection: $vm.timezone) {
            Text("Select timezone").tag(String?.none)
            ForEach(supportedTimezones, id: \.id) { tz in
                Text(tz.label).tag(Optional(tz.id))
            }
        } label: {
            Text("Timezone")
        }
        .foregroundColor(.textPrimary)
        .tint(vm.timezone == nil ? Color.accentGreenText : Color.textPrimary)
        .pickerStyle(.menu)
        .inputBordered()
    }
}

private struct ConsentCheckboxRow: View {
    @ObservedObject var vm: ConsentViewModel

    var body: some View {
        Button(action: { vm.consentChecked.toggle() }) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: vm.consentChecked ? "checkmark.square.fill" : "square")
                    .foregroundColor(vm.consentChecked ? .successGreen : .textSecondary)
                    .imageScale(.large)
                Text("By checking this box, I agree to receive recurring automated motivational SMS messages. Msg & data rates may apply. Reply STOP to cancel.")
                    .font(.footnote)
                    .foregroundColor(.textSecondary)
                    .multilineTextAlignment(.leading)
            }
        }
        .buttonStyle(.plain)
    }
}

private struct SubmitButton: View {
    @ObservedObject var phoneNumber: PhoneNumberViewModel
    @ObservedObject var consent: ConsentViewModel
    @ObservedObject var timezone: TimezoneViewModel
    let action: () -> Void

    var body: some View {
        Button("Sign up", action: action)
            .buttonStyle(PrimaryButtonStyle())
            .disabled(!(consent.consentChecked && timezone.timezone != nil && phoneNumber.phone.filter(\.isNumber).count == 10))
    }
}

private struct ReturningUserLinkButton: View {
    @ObservedObject var vm: SubmissionStatusViewModel
    let action: () -> Void

    var body: some View {
        if !vm.showSettingsLinkPrompt {
            Button("Already signed up? Get a settings link.", action: action)
                .buttonStyle(.plain)
                .foregroundColor(.accentGreenText)
                .font(.footnote)
        }
    }
}

private struct SubmissionStatusView: View {
    @ObservedObject var vm: SubmissionStatusViewModel
    let onRequestReturningUser: () -> Void

    var body: some View {
        Group {
            if vm.isLoading {
                ProgressView()
            }
            Text(vm.message)
                .font(.footnote)
                .foregroundColor(vm.message.isEmpty ? .textSecondary : .errorText)
                .padding(vm.message.isEmpty ? 0 : 8)
                .background(vm.message.isEmpty ? Color.clear : Color.errorBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(vm.message.isEmpty ? Color.clear : Color.errorBorder, lineWidth: 1)
                )

            if vm.showSettingsLinkPrompt {
                Button("Get a settings link instead", action: onRequestReturningUser)
                    .buttonStyle(.plain)
                    .foregroundColor(.accentGreenText)
                    .font(.footnote)
            }
        }
    }
}
