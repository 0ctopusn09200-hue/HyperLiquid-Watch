-- Hyperliquid Data Analysis Database Schema
-- Database: PostgreSQL 15
-- Created for Task 2: System Architecture Design

-- ============================================
-- 1. Transactions Table (原始交易记录)
-- 存储从Hyperliquid节点解析的原始交易数据
-- ============================================
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,  -- 交易哈希
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP NOT NULL,
    user_address VARCHAR(42) NOT NULL,  -- 用户地址
    coin VARCHAR(20) NOT NULL,  -- 交易对，如 BTC, ETH
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT', 'OPEN', 'CLOSE')),
    size DECIMAL(30, 8) NOT NULL,  -- 持仓大小
    price DECIMAL(30, 8) NOT NULL,  -- 成交价格
    leverage DECIMAL(5, 2),  -- 杠杆倍数
    margin DECIMAL(30, 8),  -- 保证金
    fee DECIMAL(30, 8),  -- 手续费
    tx_type VARCHAR(50),  -- 交易类型：order, liquidation等
    raw_data JSONB,  -- 原始数据（JSON格式，用于存储额外信息）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化查询性能
CREATE INDEX idx_transactions_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);
CREATE INDEX idx_transactions_block_timestamp ON transactions(block_timestamp);
CREATE INDEX idx_transactions_user_address ON transactions(user_address);
CREATE INDEX idx_transactions_coin ON transactions(coin);
CREATE INDEX idx_transactions_side ON transactions(side);
CREATE INDEX idx_transactions_tx_type ON transactions(tx_type);

-- ============================================
-- 2. Liquidations Table (清算事件)
-- 存储清算事件数据
-- ============================================
CREATE TABLE liquidations (
    id BIGSERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP NOT NULL,
    user_address VARCHAR(42) NOT NULL,
    coin VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    liquidated_size DECIMAL(30, 8) NOT NULL,  -- 被清算的仓位大小
    liquidation_price DECIMAL(30, 8) NOT NULL,  -- 清算价格
    liquidation_value_usd DECIMAL(30, 8),  -- 清算价值（USD）
    leverage DECIMAL(5, 2),
    margin DECIMAL(30, 8),
    liquidator_address VARCHAR(42),  -- 清算人地址
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_liquidations_block_timestamp ON liquidations(block_timestamp);
CREATE INDEX idx_liquidations_user_address ON liquidations(user_address);
CREATE INDEX idx_liquidations_coin ON liquidations(coin);
CREATE INDEX idx_liquidations_side ON liquidations(side);

-- ============================================
-- 3. Long Short Ratios Table (多空持仓比例)
-- 存储计算后的多空比例数据
-- ============================================
CREATE TABLE long_short_ratios (
    id BIGSERIAL PRIMARY KEY,
    coin VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    long_ratio DECIMAL(10, 4) NOT NULL,  -- 多仓比例 (0-1)
    short_ratio DECIMAL(10, 4) NOT NULL,  -- 空仓比例 (0-1)
    long_position_value DECIMAL(30, 8) NOT NULL,  -- 多仓总价值
    short_position_value DECIMAL(30, 8) NOT NULL,  -- 空仓总价值
    total_position_value DECIMAL(30, 8) NOT NULL,  -- 总持仓价值
    long_accounts INTEGER DEFAULT 0,  -- 多仓账户数
    short_accounts INTEGER DEFAULT 0,  -- 空仓账户数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin, timestamp)
);

CREATE INDEX idx_long_short_ratios_coin ON long_short_ratios(coin);
CREATE INDEX idx_long_short_ratios_timestamp ON long_short_ratios(timestamp);
CREATE INDEX idx_long_short_ratios_coin_timestamp ON long_short_ratios(coin, timestamp DESC);

-- ============================================
-- 4. Liquidation Map Table (清算地图数据)
-- 存储价格区间和对应的清算数据
-- ============================================
CREATE TABLE liquidation_map (
    id BIGSERIAL PRIMARY KEY,
    coin VARCHAR(20) NOT NULL,
    price_level DECIMAL(30, 8) NOT NULL,  -- 价格层级
    timestamp TIMESTAMP NOT NULL,
    long_liquidation_value DECIMAL(30, 8) DEFAULT 0,  -- 该价格层级的多仓清算价值
    short_liquidation_value DECIMAL(30, 8) DEFAULT 0,  -- 该价格层级的空仓清算价值
    long_liquidation_count INTEGER DEFAULT 0,  -- 多仓清算次数
    short_liquidation_count INTEGER DEFAULT 0,  -- 空仓清算次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin, price_level, timestamp)
);

CREATE INDEX idx_liquidation_map_coin ON liquidation_map(coin);
CREATE INDEX idx_liquidation_map_timestamp ON liquidation_map(timestamp);
CREATE INDEX idx_liquidation_map_coin_timestamp ON liquidation_map(coin, timestamp DESC);
CREATE INDEX idx_liquidation_map_price_level ON liquidation_map(price_level);

-- ============================================
-- 5. Positions Table (持仓快照)
-- 用于存储用户持仓快照数据（可选，用于高级分析）
-- ============================================
CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    user_address VARCHAR(42) NOT NULL,
    coin VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    size DECIMAL(30, 8) NOT NULL,
    entry_price DECIMAL(30, 8) NOT NULL,
    mark_price DECIMAL(30, 8) NOT NULL,  -- 标记价格
    leverage DECIMAL(5, 2),
    margin DECIMAL(30, 8),
    unrealized_pnl DECIMAL(30, 8),  -- 未实现盈亏
    timestamp TIMESTAMP NOT NULL,  -- 快照时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_address, coin, side, timestamp)
);

CREATE INDEX idx_positions_user_address ON positions(user_address);
CREATE INDEX idx_positions_coin ON positions(coin);
CREATE INDEX idx_positions_timestamp ON positions(timestamp);

-- ============================================
-- 6. Whale Watches Table (巨鲸地址监控)
-- 用于存储需要监控的巨鲸地址（Advanced功能）
-- ============================================
CREATE TABLE whale_watches (
    id BIGSERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL UNIQUE,
    alias VARCHAR(100),  -- 别名/标签
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_whale_watches_address ON whale_watches(wallet_address);
CREATE INDEX idx_whale_watches_active ON whale_watches(is_active);

-- ============================================
-- 7. Whale Activities Table (巨鲸活动记录)
-- 记录被监控地址的重大活动
-- ============================================
CREATE TABLE whale_activities (
    id BIGSERIAL PRIMARY KEY,
    whale_id BIGINT REFERENCES whale_watches(id),
    wallet_address VARCHAR(42) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,  -- OPEN, CLOSE, LIQUIDATION, LARGE_TRADE等
    tx_hash VARCHAR(66) NOT NULL,
    coin VARCHAR(20),
    size DECIMAL(30, 8),
    value_usd DECIMAL(30, 8),
    timestamp TIMESTAMP NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_whale_activities_whale_id ON whale_activities(whale_id);
CREATE INDEX idx_whale_activities_address ON whale_activities(wallet_address);
CREATE INDEX idx_whale_activities_timestamp ON whale_activities(timestamp DESC);
CREATE INDEX idx_whale_activities_type ON whale_activities(activity_type);

-- ============================================
-- 视图：实时多空比例视图
-- ============================================
CREATE OR REPLACE VIEW latest_long_short_ratios AS
SELECT DISTINCT ON (coin)
    coin,
    timestamp,
    long_ratio,
    short_ratio,
    long_position_value,
    short_position_value,
    total_position_value,
    long_accounts,
    short_accounts
FROM long_short_ratios
ORDER BY coin, timestamp DESC;

-- ============================================
-- 视图：最近清算事件视图
-- ============================================
CREATE OR REPLACE VIEW recent_liquidations AS
SELECT 
    tx_hash,
    block_timestamp,
    user_address,
    coin,
    side,
    liquidated_size,
    liquidation_price,
    liquidation_value_usd
FROM liquidations
ORDER BY block_timestamp DESC
LIMIT 100;

-- ============================================
-- 触发器：自动更新updated_at字段
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_whale_watches_updated_at BEFORE UPDATE ON whale_watches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
