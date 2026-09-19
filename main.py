import json
from terminal.claude_receipt_parser import parse_receipt
from terminal.claude_split_bill import split_receipt, review_split


def main():

    print("\nLoading receipt and extracting items...")
    # receipt = parse_receipt("assets/easy.png")
    receipt = parse_receipt("assets/medium.jpg")
    # receipt = parse_receipt("assets/hard.jpg")
    print("Receipt parsed successfully.")

    with open("terminal/contact_list.json", "r") as f:
        contacts = json.load(f)

    final_split = split_receipt(receipt, contacts)

    review_split(final_split)


if __name__ == "__main__":
    main()
