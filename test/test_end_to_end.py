from src.pipeline import analyze_ticket


TEST_TICKETS = [
    {
        "name": "Wi-Fi / Network",
        "ticket": "My laptop cannot connect to the office Wi-Fi."
    },
    {
        "name": "VPN",
        "ticket": "My VPN is not connecting and I cannot access the company's internal resources."
    },
    {
        "name": "Password / Access",
        "ticket": "I forgot my company password and cannot log in to my account."
    },
    {
        "name": "Hardware",
        "ticket": "My laptop screen is completely black and the computer does not respond."
    },
    {
        "name": "Software",
        "ticket": "Microsoft Outlook keeps crashing whenever I try to open it."
    },
    {
        "name": "Database Access",
        "ticket": "I cannot access the company database even though my username and password are correct."
    },
    {
        "name": "Critical Network Outage",
        "ticket": "The entire office network is down and all employees have lost internet access."
    },
    {
        "name": "Low Priority Request",
        "ticket": "Please install a new application on my laptop when you have time."
    }
]


def print_result(number, test, result):
    print("\n" + "=" * 75)
    print(f"TEST {number}: {test['name']}")
    print("=" * 75)

    print("Ticket:")
    print(test["ticket"])

    print("\nPredictions:")
    print("Category :", result["category"])
    print("Queue    :", result["queue"])
    print("Priority :", result["priority"])

    print("\nSimilar Incidents:")

    for incident in result["retrieved_incidents"]:
        print(
            f"#{incident['rank']} | "
            f"Similarity: {incident['similarity']:.3f} | "
            f"Type: {incident['type']} | "
            f"Queue: {incident['queue']} | "
            f"Priority: {incident['priority']}"
        )

    print("\nResolution:")
    print(result["resolution"])

    print("\nSTATUS: PASS")


def main():

    passed = 0
    failed = 0

    for number, test in enumerate(TEST_TICKETS, start=1):

        try:
            result = analyze_ticket(test["ticket"])

            print_result(number, test, result)

            passed += 1

        except Exception as e:

            failed += 1

            print("\n" + "=" * 75)
            print(f"TEST {number}: {test['name']}")
            print("=" * 75)

            print("STATUS: FAIL")
            print("ERROR:", repr(e))

    print("\n")
    print("=" * 75)
    print("END-TO-END TEST SUMMARY")
    print("=" * 75)

    print(f"Total tests : {len(TEST_TICKETS)}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")

    if failed == 0:
        print("\nALL END-TO-END TESTS PASSED")
    else:
        print("\nSOME END-TO-END TESTS FAILED")


if __name__ == "__main__":
    main()