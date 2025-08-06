// const fs = require("fs");
// const path = require("path");
// const { spawn } = require("child_process");
// const cloudinary = require("cloudinary").v2;

// cloudinary.config({
//     cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
//     api_key: process.env.CLOUDINARY_API_KEY,
//     api_secret: process.env.CLOUDINARY_API_SECRET,
// });

// exports.detectionImg = async (req, res) => {
//     try {
//         if (!req.file) {
//             return res.status(400).json({ error: "No image file provided" });
//         }

//         const imagePath = req.file.path.replaceAll("\\", "/");
//         console.log("📤 Uploaded image path:", imagePath);

//         const python = spawn("python", ["yolov8/detect.py", imagePath]);

//         let output = "";

//         python.stdout.on("data", (data) => {
//             output += data.toString();
//         });

//         python.stderr.on("data", (data) => {
//             console.error(`stderr: ${data}`);
//         });

//         python.on("close", async (code) => {
//             try {
//                 const detectPath = path.join(process.cwd(), 'runs', 'detect');


//                 if (!fs.existsSync(detectPath)) {
//                     fs.mkdirSync(detectPath, { recursive: true });
//                 }

//                 const subDirs = fs.readdirSync(detectPath)
//                     .map(name => ({
//                         name,
//                         fullPath: path.join(detectPath, name),
//                     }))
//                     .filter(entry => fs.statSync(entry.fullPath).isDirectory())
//                     .sort((a, b) => {
//                         return fs.statSync(b.fullPath).mtimeMs - fs.statSync(a.fullPath).mtimeMs;
//                     })
//                     .map(entry => entry.name); // กลับมาเป็นแค่ชื่อโฟลเดอร์

//                 const latestDir = subDirs[0];
//                 const resultDirPath = path.join(detectPath, latestDir);

//                 const resultFiles = fs.readdirSync(resultDirPath).filter(file =>
//                     /\.(jpg|jpeg|png|webp)$/i.test(file)
//                 );

//                 if (resultFiles.length === 0) {
//                     throw new Error("No image files found in result folder");
//                 }

//                 const resultImageFile = resultFiles[0];
//                 const resultImgPath = path.join(resultDirPath, resultImageFile);

//                 // ⬆️ Upload to Cloudinary
//                 const uploadResult = await cloudinary.uploader.upload(resultImgPath, {
//                     folder: "detections"
//                 });

//                 console.log("🌐 Cloudinary URL:", uploadResult.secure_url);


//                 // ✅ ส่ง response ก่อน
//                 if (!res.headersSent) {
//                     res.json({
//                         result: output.trim(),
//                         imageUrl: uploadResult.secure_url,
//                     });
//                 }

//                 // 🧹 ลบภาพต้นฉบับที่อัปโหลดไว้ชั่วคราว
//                 fs.unlink(imagePath, (err) => {
//                     if (err) {
//                         console.error("❌ Failed to delete original uploaded image:", err);
//                     } else {
//                         console.log("🧹 Deleted original uploaded image:", imagePath);
//                     }
//                 });

//                 // 🧹 ลบไฟล์หลังส่ง response แล้ว
//                 fs.rm(resultDirPath, { recursive: true, force: true }, (err) => {
//                     if (err) {
//                         console.error("Failed to delete detection result folder:", err);
//                     } else {
//                         console.log("🧹 Deleted detection folder:", resultDirPath);
//                     }
//                 });

//             } catch (err) {
//                 console.error("Error reading detection folder:", err);
//                 if (!res.headersSent) {
//                     res.status(500).json({ error: "Detection folder read failed" });
//                 }
//             }
//         });
//     } catch (error) {
//         console.error("Internal server error:", error);
//         if (!res.headersSent) {
//             res.status(500).json({ error: "Internal server error" });
//         }
//     }
// };

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const cloudinary = require("cloudinary").v2;

cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
});

exports.detectionImg = async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });

    const imagePath = req.file.path.replaceAll("\\", "/");
    const python = spawn("python", ["yolov8/detect.py", imagePath]);

    let output = "", errorOutput = "";

    python.stdout.on("data", data => output += data.toString());
    python.stderr.on("data", data => errorOutput += data.toString());

    python.on("close", async code => {
        try {
            if (code !== 0) throw new Error(errorOutput.trim() || `Python failed with exit code ${code}`);
            await new Promise(resolve => setTimeout(resolve, 1500));

            const detectDirs = [
                path.resolve(process.cwd(), "runs", "detect"),
                path.resolve(__dirname, "..", "runs", "detect"),
                path.resolve("./runs/detect"),
            ];

            let resultImgPath = null;

            for (const dir of detectDirs) {
                if (!fs.existsSync(dir)) continue;
                const subDirs = fs.readdirSync(dir)
                    .map(name => ({
                        fullPath: path.join(dir, name),
                        mtime: fs.statSync(path.join(dir, name)).mtimeMs
                    }))
                    .filter(d => fs.statSync(d.fullPath).isDirectory())
                    .sort((a, b) => b.mtime - a.mtime);

                if (subDirs.length === 0) continue;

                const resultFiles = fs.readdirSync(subDirs[0].fullPath)
                    .filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f));

                if (resultFiles.length > 0) {
                    resultImgPath = path.join(subDirs[0].fullPath, resultFiles[0]);
                    break;
                }
            }

            if (!resultImgPath || !fs.existsSync(resultImgPath)) {
                throw new Error("Result image not found");
            }

            const uploadResult = await cloudinary.uploader.upload(resultImgPath, { folder: "detections" });

            if (!res.headersSent) {
                res.json({
                    result: output.trim(),
                    imageUrl: uploadResult.secure_url,
                });
            }

            cleanup(imagePath, path.dirname(resultImgPath));

        } catch (err) {
            console.error("❌ Detection error:", err);
            if (!res.headersSent) {
                res.status(500).json({ error: err.message });
            }
            cleanup(imagePath);
        }
    });

    python.on("error", err => {
        console.error("❌ Python error:", err);
        if (!res.headersSent) res.status(500).json({ error: err.message });
    });
};

function cleanup(original, dir = null) {
    if (fs.existsSync(original)) fs.unlink(original, () => {});
    if (dir && fs.existsSync(dir)) fs.rm(dir, { recursive: true, force: true }, () => {});
}
