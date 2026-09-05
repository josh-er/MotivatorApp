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
            PhoneNumberField(vm: vm.phoneNumber)
            DeliveryTimePicker(vm: vm.deliveryTime)
            TimezonePicker(vm: vm.timezone)
            ConsentCheckboxRow(vm: vm.consent)

            SubmitButton(consent: vm.consent, timezone: vm.timezone, action: vm.signUp)

            ReturningUserLinkButton(vm: vm.submissionStatus, action: onRequestReturningUser)

            SubmissionStatusView(vm: vm.submissionStatus, onRequestReturningUser: onRequestReturningUser)

            Spacer()
        }
        .padding()
    }
}

private struct PhoneNumberField: View {
    @ObservedObject var vm: PhoneNumberViewModel

    var body: some View {
        TextField("Phone number", text: $vm.phone)
            .textFieldStyle(.roundedBorder)
            .keyboardType(.phonePad)
    }
}

private struct DeliveryTimePicker: View {
    @ObservedObject var vm: DeliveryTimeViewModel

    var body: some View {
        DatePicker(
            "Delivery time",
            selection: $vm.selectedTime,
            displayedComponents: .hourAndMinute
        )
        .datePickerStyle(.compact)
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
        .pickerStyle(.menu)
    }
}

private struct ConsentCheckboxRow: View {
    @ObservedObject var vm: ConsentViewModel

    var body: some View {
        Button(action: { vm.consentChecked.toggle() }) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: vm.consentChecked ? "checkmark.square.fill" : "square")
                    .foregroundColor(vm.consentChecked ? .accentColor : .secondary)
                    .imageScale(.large)
                Text("By checking this box, I agree to receive recurring automated motivational SMS messages. Msg & data rates may apply. Reply STOP to cancel.")
                    .font(.footnote)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.leading)
            }
        }
        .buttonStyle(.plain)
    }
}

private struct SubmitButton: View {
    @ObservedObject var consent: ConsentViewModel
    @ObservedObject var timezone: TimezoneViewModel
    let action: () -> Void

    var body: some View {
        Button("Sign up", action: action)
            .buttonStyle(.borderedProminent)
            .disabled(!(consent.consentChecked && timezone.timezone != nil))
    }
}

private struct ReturningUserLinkButton: View {
    @ObservedObject var vm: SubmissionStatusViewModel
    let action: () -> Void

    var body: some View {
        if !vm.showSettingsLinkPrompt {
            Button("Already signed up? Get a settings link.", action: action)
                .buttonStyle(.bordered)
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
                .foregroundColor(.gray)

            if vm.showSettingsLinkPrompt {
                Button("Get a settings link instead", action: onRequestReturningUser)
                    .buttonStyle(.bordered)
                    .font(.footnote)
            }
        }
    }
}
