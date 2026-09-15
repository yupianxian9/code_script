# GitHub cli上传release

## 1.安装与认证

下载安装好后使用下面的命令进行认证:

```
gh auth login
```

根据提示来，使用网络认证最方便。

## 2.定位仓库

**确保你在正确的目录**：打开终端，`cd` 到你本地的项目仓库目录下。`gh` 命令会自动识别当前目录对应的 GitHub 仓库。

## 3.上传操作（建议使用本地仓库上传，速度更快）

**场景一：创建新 Release 并上传**

```powershell
cd D:\Code\my-app
gh release create v1.0.0 "D:\code\game\AUGUST\**" --title "v1.0.0 August" --notes "upload"
```

**场景二：向已有 Release 补充上传**

```powershell
gh release upload v1.0.0 "D:/Code/my-app/build/**"
```

---

## 4.直接远程定位仓库并上传

**场景一：创建新 Release 并上传**

```
gh release create v1.0.1 "D:\code\game\Bishop\**" -R yupianxian9/dawn --title "v1.0.1 Bishop" --notes "Bishop"
```

**场景二：向已有 Release 补充上传**

```
gh release upload v1.0.0 "D:/MyApp/dist/**" -R yourname/my-repo
```