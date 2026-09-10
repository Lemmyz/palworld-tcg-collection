USE PalworldTCG;
GO

DECLARE @SetID INT;

SELECT @SetID = SetID
FROM dbo.CardSets
WHERE SetCode = 'EBP01';


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.Cards
    WHERE SetID = @SetID
      AND CardNumber = 'EBP01-001'
      AND Variant = 'Standard'
)
BEGIN
    INSERT INTO dbo.Cards
    (
        SetID,
        CardNumber,
        CardName,
        CardType,
        CardColour,
        Rarity,
        Variant
    )
    VALUES
    (
        @SetID,
        'EBP01-001',
        'Jormuntide Ignis - Savage Lava Dragon',
        'Pal',
        'Red',
        'RR',
        'Standard'
    );
END;


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.Cards
    WHERE SetID = @SetID
      AND CardNumber = 'EBP01-002'
      AND Variant = 'Standard'
)
BEGIN
    INSERT INTO dbo.Cards
    (
        SetID,
        CardNumber,
        CardName,
        CardType,
        CardColour,
        Rarity,
        Variant
    )
    VALUES
    (
        @SetID,
        'EBP01-002',
        'Suzaku - Hellfire Wings',
        'Pal',
        'Red',
        'RR',
        'Standard'
    );
END;


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.Cards
    WHERE SetID = @SetID
      AND CardNumber = 'EBP01-003'
      AND Variant = 'Standard'
)
BEGIN
    INSERT INTO dbo.Cards
    (
        SetID,
        CardNumber,
        CardName,
        CardType,
        CardColour,
        Rarity,
        Variant
    )
    VALUES
    (
        @SetID,
        'EBP01-003',
        'Gobfin Ignis - Blazing Hothead',
        'Pal',
        'Red',
        'R',
        'Standard'
    );
END;
GO