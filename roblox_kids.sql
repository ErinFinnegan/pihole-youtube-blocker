INSERT OR IGNORE INTO domainlist (type,domain,enabled,comment) VALUES
(3,'^(.+\\.)*roblox\\.com$',1,'KidsRestricted Roblox'),
(3,'^(.+\\.)*rbxcdn\\.com$',1,'KidsRestricted Roblox CDN'),
(3,'^(.+\\.)*rbxtrk\\.com$',1,'KidsRestricted Roblox tracking');

INSERT OR IGNORE INTO domainlist_by_group (domainlist_id,group_id)
SELECT d.id,g.id
FROM domainlist d
JOIN "group" g ON g.name='KidsRestricted'
WHERE d.domain IN (
  '^(.+\\.)*roblox\\.com$',
  '^(.+\\.)*rbxcdn\\.com$',
  '^(.+\\.)*rbxtrk\\.com$'
);


