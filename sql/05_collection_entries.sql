USE PalworldTCG;
GO

-- Additive and safe to rerun; preserves the original collection and card IDs.
IF OBJECT_ID('dbo.CollectionEntries', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CollectionEntries (
        CollectionEntryID INT IDENTITY(1,1) PRIMARY KEY,
        CardID INT NOT NULL REFERENCES dbo.Cards(CardID),
        Quantity INT NOT NULL DEFAULT 1,
        CardCondition NVARCHAR(30) NOT NULL DEFAULT 'Near Mint',
        PurchasePricePerCard DECIMAL(10,2) NULL,
        DateAcquired DATE NULL,
        StorageLocation NVARCHAR(100) NULL,
        IsForTrade BIT NOT NULL DEFAULT 0,
        CONSTRAINT CK_CollectionEntries_Quantity CHECK (Quantity > 0),
        CONSTRAINT CK_CollectionEntries_Price CHECK (PurchasePricePerCard IS NULL OR PurchasePricePerCard >= 0)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_CollectionEntries_CardID'
               AND object_id = OBJECT_ID('dbo.CollectionEntries'))
    CREATE INDEX IX_CollectionEntries_CardID ON dbo.CollectionEntries(CardID);
GO
