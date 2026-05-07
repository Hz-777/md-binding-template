# 输入文件说明

把你的蛋白质和配体文件放在这个目录下：

## 必需文件

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `protein.pdb` | PDB | 蛋白质结构，可以直接来自 PDB 数据库或 AlphaFold |
| `ligand.sdf` | SDF | 配体结构，需要有 3D 坐标（可以从 ChemDraw / Avogadro 导出） |

## 对蛋白质文件的要求

- 移除结晶水和非标准残基（脚本会自动处理，但最好预先检查）
- 如果 PDB 文件里有多条链，确认目标链存在
- 缺失环区较多的蛋白需要先用同源建模补全（推荐 MODELLER 或 AlphaFold2）

## 对配体文件的要求

- **必须有 3D 坐标**（不能只有 SMILES）
- 推荐先用 Avogadro / RDKit / Chem3D 做力场预优化
- 配体净电荷在 `config/params.yaml` 里的 `ligand_charge` 字段设置
- SDF 中包含的是**对接后的结合位点构象**（如果有对接结果，直接用对接 pose）

## 快速获取配体 3D 构象

如果只有 SMILES，可以用这个命令生成 SDF：

```bash
conda run -n mdenv python3 - <<'EOF'
from rdkit import Chem
from rdkit.Chem import AllChem

smiles = "YOUR_SMILES_HERE"
mol = Chem.MolFromSmiles(smiles)
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
AllChem.MMFFOptimizeMolecule(mol)
with Chem.SDWriter("inputs/ligand.sdf") as w:
    w.write(mol)
print("Done: inputs/ligand.sdf")
EOF
```
