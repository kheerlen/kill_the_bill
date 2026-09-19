from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

def get_people(contacts):
    available = list(contacts.keys())
    completer = WordCompleter(available, ignore_case=True)

    print("\nAvailable people:")
    print(", ".join(available))
    print("\nType names separated by commas. Press TAB for autocomplete.")

    raw = prompt("\nWho ate together?\n> ", completer=completer)

    selected = [p.strip() for p in raw.split(",") if p.strip()]

    invalid = [p for p in selected if p not in contacts]
    if invalid:
        raise ValueError(f"Unknown people: {', '.join(invalid)}")

    return selected

def paid_items(receipt):
    return [item for item in receipt["items"] if float(item["total_price"]) > 0]


def show_items(receipt):
    print("\nReceipt items:")
    items = paid_items(receipt)

    for i, item in enumerate(items, start=1):
        name = item["name"]
        quantity = item.get("quantity", 1)
        unit_price = item.get("unit_price", item["total_price"])
        total_price = item["total_price"]

        print(f"{i}. {name}")
        print(f"   {quantity} × €{unit_price} = €{total_price}")


def get_assignments(receipt, people):
    assignments = {}
    items = paid_items(receipt)

    completer = WordCompleter(people + ["everyone"], ignore_case=True)

    print("\nPeople:", ", ".join(people))
    print("For each item, type who had it.")
    print("Press TAB to autocomplete from selected people only.")
    print("Examples:")
    print("- everyone")
    print(f"- {people[0]}")
    if len(people) > 1:
        print(f"- {people[0]}, {people[1]}")

    for i, item in enumerate(items, start=1):
        quantity = item.get("quantity", 1)
        unit_price = item.get("unit_price", item["total_price"])
        description = item.get("description", "")

        print(f"\nItem {i}: {item['name']}")
        if description:
            print(f"({description})")
        print(f"{quantity} × €{unit_price}")

        answer = prompt("Who had this?\n> ", completer=completer).strip()

        if answer.lower() == "everyone":
            assignments[i - 1] = people
        else:
            selected = [p.strip() for p in answer.split(",") if p.strip()]

            invalid = [p for p in selected if p not in people]
            if invalid:
                raise ValueError(
                    f"These people were not selected for this meal: {', '.join(invalid)}"
                )

            assignments[i - 1] = selected

    return assignments

def calculate_split(receipt, people, assignments):
    totals = {person: 0.0 for person in people}
    details = {person: [] for person in people}

    items = paid_items(receipt)

    for idx, item in enumerate(items):
        name = item["name"]
        quantity = float(item.get("quantity", 1))
        unit_price = float(item.get("unit_price", item["total_price"]))
        total_price = float(item["total_price"])

        assigned_people = assignments.get(idx, [])

        if not assigned_people:
            continue

        share_amount = total_price / len(assigned_people)
        share_quantity = quantity / len(assigned_people)

        for person in assigned_people:
            totals[person] += share_amount
            details[person].append({
                "item": name,
                "quantity": round(share_quantity, 2),
                "amount": round(share_amount, 2)
            })

    items_sum = sum(float(item["total_price"]) for item in items)
    receipt_total = float(receipt["total"])
    extra = receipt_total - items_sum

    if abs(extra) > 0.01 and items_sum > 0:
        for person in totals:
            proportion = totals[person] / items_sum
            extra_share = extra * proportion
            totals[person] += extra_share

            if abs(extra_share) > 0.01:
                details[person].append({
                    "item": "tax/service/rounding",
                    "quantity": 1,
                    "amount": round(extra_share, 2)
                })

    return {
        person: {
            "total": round(totals[person], 2),
            "items": details[person]
        }
        for person in people
    }

def split_receipt(receipt, contacts):
    show_items(receipt)
    people = get_people(contacts)    
    # people = get_people()
    assignments = get_assignments(receipt, people)
    final_split = calculate_split(receipt, people, assignments)

    return final_split

def review_split(final_split):
    print("\n" + "=" * 60)
    print("FINAL REVIEW")
    print("=" * 60)

    total = 0.0

    for person, info in final_split.items():
        amount = info["total"]
        total += amount

        print(f"\n{person}: €{amount:.2f}")

        for item in info["items"]:
            print(
                f"  - {item['item']}: "
                f"{item['quantity']} portion(s), "
                f"€{item['amount']:.2f}"
            )

    print("\n" + "-" * 60)
    print(f"TOTAL: €{total:.2f}")
    print("=" * 60)