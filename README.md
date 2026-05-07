# MD Binding Free Energy Template

[![CI](https://github.com/YOUR_USERNAME/md-binding-template/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/md-binding-template/actions)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_USERNAME/md-binding-template)

上传蛋白质（PDB）和配体（SDF）文件，一键完成分子动力学模拟和 MM-PB/GBSA 结合自由能分析。

## 工作流程

```
inputs/protein.pdb  ─┐
inputs/ligand.sdf   ─┤
                      ▼
               ┌─ Step 1: 蛋白质清洗 (pdbfixer) ──────────┐
               ├─ Step 2: 配体参数化 (acpype + GAFF2) ───┤
               │                                           │
               └───────────────────────────────────────────┘
                              ▼
                  Step 3: 构建复合物拓扑 (pdb2gmx)
                              ▼
                  Step 4: 溶剂化 + 加离子 (gmx solvate)
                              ▼
                  Step 5: MD模拟 (GROMACS)
                    ├── 能量最小化 (EM)
                    ├── NVT 平衡  200 ps
                    ├── NPT 平衡  200 ps
                    └── 生产 MD   10 ns (可配置)
                              ▼
                  Step 6: 结合自由能 (gmx_MMPBSA)
                    ├── MM-GBSA ΔG binding
                    └── 残基能量分解
                              ▼
                  Step 7: 分析报告
                    ├── RMSD 图 (蛋白骨架 + 配体)
                    ├── 能量分解柱状图
                    └── results/report.html
```

## 快速开始

### 方式一：GitHub Codespaces（最简单，无需安装）

1. 点击页面右上角 **"Use this template"** → **"Open in a codespace"**
2. 等待环境构建完成（约 5–10 min）
3. 上传文件：
   ```bash
   # 把你的文件拖入 Codespaces 的 inputs/ 目录，或者：
   cp /path/to/your/protein.pdb inputs/
   cp /path/to/your/ligand.sdf  inputs/
   ```
4. 运行：
   ```bash
   make run
   ```

### 方式二：本地 Docker（跨平台，隔离环境）

```bash
# 克隆模板
git clone https://github.com/YOUR_USERNAME/md-binding-template.git
cd md-binding-template

# 放入输入文件
cp /path/to/protein.pdb inputs/
cp /path/to/ligand.sdf  inputs/

# 一键运行（自动构建镜像 + 运行全流程）
docker-compose up

# 或者指定核心数
CORES=8 docker-compose up
```

### 方式三：云服务器 / 实验室服务器（有 conda 环境）

```bash
# 创建 conda 环境（只需一次，约 10–15 min）
conda env create -f environment.yml
conda activate mdenv

# 放入输入文件
cp protein.pdb inputs/
cp ligand.sdf  inputs/

# 运行（-c 指定核心数）
./run.sh
# 或者：
snakemake --snakefile workflow/Snakefile -c 16
```

### 方式四：HPC 集群（Slurm）

```bash
# 提交 Snakemake 作业（会自动调度各步骤）
snakemake \
  --snakefile workflow/Snakefile \
  --cluster "sbatch --ntasks={threads} --mem=16G --time=24:00:00 --partition=gpu" \
  --jobs 4
```

## 配置说明

编辑 `config/params.yaml` 调整参数：

```yaml
system:
  ligand_charge: 0          # 配体净电荷 ← 必须填正确！
  ligand_ff: "gaff2"        # 配体力场
  protein_ff: "charmm36m"   # 蛋白质力场

md:
  prod_steps: 5000000       # 生产 MD 步数 (10 ns)
  temp: 300                 # 温度 K

mmpbsa:
  endframe: 500             # 用多少帧做 MMPBSA
  interval: 5               # 每隔几帧取一次

gpu:
  enabled: false            # 有 GPU 时改为 true
  gpu_id: 0
```

## 输出文件

```
results/
├── report.html                          # ← 主要结果报告（用浏览器打开）
├── mmpbsa/
│   ├── FINAL_RESULTS_MMPBSA.dat         # ΔG binding 数值
│   └── MMPBSA_DECOMP.dat                # 残基能量分解
└── plots/
    ├── rmsd.png                         # RMSD 轨迹图
    └── mmpbsa_decomposition.png         # 能量分解柱状图

work/                                    # 中间文件（可删除）
└── 05_md/
    ├── md.xtc                           # 完整轨迹（用 VMD/PyMOL 可视化）
    └── md.tpr                           # 拓扑 + 参数
```

## 技术栈

| 功能 | 软件 | 说明 |
|------|------|------|
| MD 引擎 | [GROMACS 2024](https://www.gromacs.org) | 支持 CPU/GPU |
| 蛋白质处理 | [PDBFixer](https://github.com/openmm/pdbfixer) | 补全缺失残基、加氢 |
| 配体参数化 | [acpype](https://github.com/alanwilter/acpype) + GAFF2 | AM1-BCC 电荷 |
| 结合自由能 | [gmx_MMPBSA](https://valdes-tresanco-ms.github.io/gmx_MMPBSA/) | MM-PB/GBSA |
| 轨迹分析 | [MDAnalysis](https://www.mdanalysis.org) | RMSD、选择 |
| 流程管理 | [Snakemake](https://snakemake.github.io) | 断点续跑、并行 |
| 容器化 | Docker + devcontainer | 跨平台一致环境 |

## 常见问题

**Q: 配体参数化失败 (acpype error)**  
A: 检查 `config/params.yaml` 里的 `ligand_charge` 是否正确，配体 SDF 是否有完整 3D 坐标。

**Q: gmx pdb2gmx 报错找不到残基**  
A: 蛋白可能包含非标准残基（修饰氨基酸、金属中心等），需要提供对应的 `.rtp` 参数文件。

**Q: MM-GBSA ΔG 不准确**  
A: MM-PB/GBSA 精度约 ±2–5 kcal/mol，适合相对排序，不适合绝对预测。提高 `endframe` 增加采样。

**Q: 如何用 GPU 加速？**  
A: 设置 `config/params.yaml` 中 `gpu.enabled: true`，并确保安装了 CUDA 版 GROMACS（需从源码编译或使用 NVIDIA NGC 容器）。

**Q: 模拟多少 ns 合适？**  
A: 入门测试 5 ns，正式计算 50–200 ns，弹性蛋白/构象变化需要更长。调整 `md.prod_steps` 参数。

## 引用

如果使用了这个模板，请引用以下核心软件：

- GROMACS: Abraham et al., *SoftwareX* (2015)
- gmx_MMPBSA: Valdés-Tresanco et al., *J. Chem. Theory Comput.* (2021)
- GAFF2/acpype: Wang et al., *J. Comput. Chem.* (2004)

## License

MIT
