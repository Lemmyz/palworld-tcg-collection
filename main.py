from database import get_connection


def display_card_sets():
    query = """
        SELECT
            SetCode,
            SetName,
            ReleaseDate
        FROM dbo.CardSets
        ORDER BY ReleaseDate;
    """

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        card_sets = cursor.fetchall()

    print("PALWORLD TCG CARD SETS")
    print("-" * 40)

    if not card_sets:
        print("No card sets found.")
        return

    for card_set in card_sets:
        print(
            f"{card_set.SetCode} - "
            f"{card_set.SetName} "
            f"({card_set.ReleaseDate})"
        )


if __name__ == "__main__":
    display_card_sets()