USE PalworldTCG;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.CardSets
    WHERE SetCode = 'EBP01'
)
BEGIN
    INSERT INTO dbo.CardSets
    (
        SetCode,
        SetName,
        ReleaseDate
    )
    VALUES
    (
        'EBP01',
        'Dawn of Palpagos',
        '2026-07-30'
    );
END;
GO