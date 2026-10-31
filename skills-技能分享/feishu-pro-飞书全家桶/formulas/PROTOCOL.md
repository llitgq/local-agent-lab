---
name: feishu-doc-gongshi
description: 将中文数学公式/经济公式转化为飞书文档可用的 LaTeX 公式（KaTeX 引擎）
---

# 飞书文档公式撰写指南

将中文数学公式、经济公式转换为飞书文档中的 LaTeX 公式字符串。
飞书文档使用 KaTeX 引擎渲染，支持标准 LaTeX 语法。

## 核心转换规则

### 1. 中文标注 → `\text{中文}`

公式中的中文变量名、标注、说明，统一用 `\text{}` 包裹：

```
增长率 → \text{增长率}
基期量 → \text{基期量}
其中 a=b → \text{其中}\ a=b
```

### 2. 除法 → `\frac{分子}{分母}`

推荐将 ÷ 转换为分式形式（更清晰），也可保留 `\div`：

```
增长量 ÷ 基期量 → \frac{\text{增长量}}{\text{基期量}}
a ÷ b → \frac{a}{b}
也可用: a \div b
```

### 3. 等号链 → 直接用 `=` 连接

多个等价变形直接用 `=` 串联：

```
\text{增长率}=\frac{\text{增长量}}{\text{基期量}}=\frac{\text{现期量}-\text{基期量}}{\text{基期量}}=\frac{\text{现期量}}{\text{基期量}}-1
```

### 4. 上下标

```
上标: x^2, x^{n+1}
下标: x_1, x_{i+j}
```

### 5. 多行公式

使用 `\\` 换行，`&` 对齐：

```latex
\begin{aligned}
\text{增长率} &= \frac{\text{增长量}}{\text{基期量}} \\
&= \frac{\text{现期量}-\text{基期量}}{\text{基期量}} \\
&= \frac{\text{现期量}}{\text{基期量}} - 1
\end{aligned}
```

## 常用数学符号速查

| 含义 | LaTeX |
|------|-------|
| 分数 a/b | `\frac{a}{b}` |
| 除号 ÷ | `\div` |
| 乘号 × | `\times` |
| 根号 √x | `\sqrt{x}` |
| n次根号 | `\sqrt[n]{x}` |
| 大于等于 | `\geqslant` |
| 小于等于 | `\leqslant` |
| 不等于 | `\not=` |
| 约等于 | `\approx` |
| 无穷大 | `\infty` |
| 百分号 | `\%` |
| 求和 | `\sum_{i=1}^{n}` |
| 积分 | `\int_{a}^{b}` |
| 连乘 | `\prod` |
| 绝对值 | `\left\| x \right\|` |
| 向量 | `\vec{a}` |
| 箭头 | `\rightarrow`, `\Rightarrow` |

## 常用希腊字母

| 字母 | 小写 | 大写 |
|------|------|------|
| α | `\alpha` | `\Alpha` |
| β | `\beta` | `\Beta` |
| γ | `\gamma` | `\Gamma` |
| δ | `\delta` | `\Delta` |
| θ | `\theta` | `\Theta` |
| λ | `\lambda` | `\Lambda` |
| μ | `\mu` | `\Mu` |
| π | `\pi` | `\Pi` |
| σ | `\sigma` | `\Sigma` |
| φ | `\phi` | `\Phi` |
| ω | `\omega` | `\Omega` |

## 常用结构

### 分段函数 / 条件表达式

```latex
f(x) = \begin{cases}
a & \text{if } b \\
c & \text{if } d
\end{cases}
```

### 矩阵

```latex
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
```

圆括号矩阵 `pmatrix`，方括号 `bmatrix`，花括号 `Bmatrix`，行列式 `vmatrix`

### 标注/括号

```latex
\overbrace{a+b+c}^{\text{标注}}
\underbrace{a+b+c}_{\text{标注}}
\boxed{E=mc^2}
```

## 飞书文档插入方式

| 方式 | 操作 |
|------|------|
| 最快 | 在任意位置输入 `$$公式$$`（`$$` 和公式之间不能有空格） |
| 斜杠命令 | 输入 `/gs` 或 `/eq` + Enter |
| 工具列表 | 输入 `/` → 选择「公式」 |
| 加号菜单 | 空白行行首点击 `+` → 选择「公式」 |

## 公考·资料分析常用公式模板

### 增长率

```latex
\text{增长率}=\frac{\text{增长量}}{\text{基期量}}=\frac{\text{现期量}-\text{基期量}}{\text{基期量}}=\frac{\text{现期量}}{\text{基期量}}-1=\frac{\text{增长量}}{\text{现期量}-\text{增长量}}
```

### 基期量

```latex
\text{基期量}=\frac{\text{现期量}}{1+\text{增长率}}=\text{现期量}-\text{增长量}
```

### 增长量

```latex
\text{增长量}=\text{现期量} \times \frac{\text{增长率}}{1+\text{增长率}}=\text{基期量} \times \text{增长率}
```

### 比重

```latex
\text{比重}=\frac{\text{部分量}}{\text{整体量}}
```

### 平均数

```latex
\text{平均数}=\frac{\text{总量}}{\text{总个数}}
```

### 倍数

```latex
\text{A}=\text{B} \times N \quad \text{(A 是 B 的 N 倍)}
```

## 输出格式

当用户给出一个公式要求转换时，按以下格式输出：

1. **原始公式**（用户给出的文本形式）
2. **LaTeX 公式**（飞书文档可直接粘贴使用的代码）
3. **$$ 格式**（用 `$$...$$` 包裹的完整格式，方便直接粘贴到文档）

示例：

> **原始公式**: 增长率 = 增长量 ÷ 基期量
>
> **LaTeX**: `\text{增长率}=\frac{\text{增长量}}{\text{基期量}}`
>
> **粘贴到文档**: `$$\text{增长率}=\frac{\text{增长量}}{\text{基期量}}$$`

## 参考资料

- 飞书帮助中心：[在文档中使用公式](https://www.feishu.cn/hc/zh-CN/articles/894598450617)
- 飞书帮助中心：[文档支持的公式](https://www.feishu.cn/hc/zh-CN/articles/014150532397)
- KaTeX 官网：https://katex.org/docs/supported

## 注意事项

- 飞书文档不支持所有 KaTeX 公式，个别复杂公式可能显示异常，以实际渲染结果为准
- `\text{}` 中的中文可以正常显示，不需要额外配置
- 如果用户没有明确要求分式形式，除法也可用 `\div` 表示
- 多行公式中 `\\` 是换行，`&` 是对齐点
- 多行公式环境（equation/align 等）会自动编号，加 `\nonumber` 或 `\notag` 可取消
