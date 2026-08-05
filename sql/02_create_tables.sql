USE PalworldTCG;
GO

IF OBJECT_ID('dbo.CardSets', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CardSets
    (
        SetID INT IDENTITY(1,1) PRIMARY KEY,
        SetCode NVARCHAR(20) NOT NULL UNIQUE,
        SetName NVARCHAR(100) NOT NULL,
        ReleaseDate DATE NULL
    );
END;
GO

IF OBJECT_ID('dbo.Cards', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Cards
    (
        CardID INT IDENTITY(1,1) PRIMARY KEY,
        SetID INT NOT NULL,
        CardNumber NVARCHAR(20) NOT NULL,
        CardName NVARCHAR(100) NOT NULL,
        CardType NVARCHAR(30) NOT NULL,
        CardColour NVARCHAR(30) NULL,
        Rarity NVARCHAR(20) NOT NULL,
        Variant NVARCHAR(50) NOT NULL DEFAULT 'Standard',

        CONSTRAINT FK_Cards_CardSets
            FOREIGN KEY (SetID)
            REFERENCES dbo.CardSets(SetID),

        CONSTRAINT UQ_Cards_Set_Number_Variant
            UNIQUE (SetID, CardNumber, Variant)
    );
END;
GO