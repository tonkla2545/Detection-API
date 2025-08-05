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
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No image file provided" });
        }

        const imagePath = req.file.path.replaceAll("\\", "/");
        console.log("📤 Uploaded image path:", imagePath);

        const python = spawn("python", ["yolov8/detect.py", imagePath]);

        let output = "";

        python.stdout.on("data", (data) => {
            output += data.toString();
        });

        python.stderr.on("data", (data) => {
            console.error(`stderr: ${data}`);
        });

        python.on("close", async (code) => {
            try {
                // More robust path handling
                const detectPath = path.resolve(process.cwd(), 'runs', 'detect');
                console.log("🔍 Looking for detection results in:", detectPath);

                // Wait a bit for YOLOv8 to finish writing files
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Check if the detect directory exists
                if (!fs.existsSync(detectPath)) {
                    console.error("❌ Detection directory doesn't exist:", detectPath);

                    // Try alternative paths
                    const altPaths = [
                        path.resolve(__dirname, '..', 'runs', 'detect'),
                        path.resolve(__dirname, '..', '..', 'runs', 'detect'),
                        path.resolve('./runs/detect'),
                        path.resolve('./yolov8/runs/detect')
                    ];

                    let foundPath = null;
                    for (const altPath of altPaths) {
                        if (fs.existsSync(altPath)) {
                            foundPath = altPath;
                            console.log("✅ Found detection directory at:", altPath);
                            break;
                        }
                    }

                    if (!foundPath) {
                        throw new Error(`Detection directory not found. Searched paths: ${[detectPath, ...altPaths].join(', ')}`);
                    }

                    detectPath = foundPath;
                }

                // Get subdirectories with error handling
                let subDirs;
                try {
                    const dirContents = fs.readdirSync(detectPath);
                    subDirs = dirContents
                        .map(name => ({
                            name,
                            fullPath: path.join(detectPath, name),
                        }))
                        .filter(entry => {
                            try {
                                return fs.statSync(entry.fullPath).isDirectory();
                            } catch (err) {
                                console.warn(`⚠️ Cannot stat ${entry.fullPath}:`, err.message);
                                return false;
                            }
                        })
                        .sort((a, b) => {
                            try {
                                return fs.statSync(b.fullPath).mtimeMs - fs.statSync(a.fullPath).mtimeMs;
                            } catch (err) {
                                console.warn(`⚠️ Cannot compare timestamps:`, err.message);
                                return 0;
                            }
                        })
                        .map(entry => entry.name);
                } catch (err) {
                    throw new Error(`Failed to read detection directory: ${err.message}`);
                }

                if (subDirs.length === 0) {
                    throw new Error(`No subdirectories found in ${detectPath}`);
                }

                const latestDir = subDirs[0];
                const resultDirPath = path.join(detectPath, latestDir);
                console.log("📁 Using result directory:", resultDirPath);

                // Check if result directory exists and has files
                if (!fs.existsSync(resultDirPath)) {
                    throw new Error(`Result directory doesn't exist: ${resultDirPath}`);
                }

                const resultFiles = fs.readdirSync(resultDirPath).filter(file =>
                    /\.(jpg|jpeg|png|webp)$/i.test(file)
                );

                if (resultFiles.length === 0) {
                    const allFiles = fs.readdirSync(resultDirPath);
                    throw new Error(`No image files found in result folder. Found files: ${allFiles.join(', ')}`);
                }

                const resultImageFile = resultFiles[0];
                const resultImgPath = path.join(resultDirPath, resultImageFile);
                console.log("🖼️ Processing result image:", resultImgPath);

                // Verify the result image exists
                if (!fs.existsSync(resultImgPath)) {
                    throw new Error(`Result image file doesn't exist: ${resultImgPath}`);
                }

                // ⬆️ Upload to Cloudinary
                const uploadResult = await cloudinary.uploader.upload(resultImgPath, {
                    folder: "detections"
                });

                console.log("🌐 Cloudinary URL:", uploadResult.secure_url);

                // ✅ Send response
                if (!res.headersSent) {
                    res.json({
                        result: output.trim(),
                        imageUrl: uploadResult.secure_url,
                    });
                }

                // 🧹 Clean up files after successful response
                cleanup(imagePath, resultDirPath);

            } catch (err) {
                console.error("❌ Error in detection processing:", err.message);
                console.error("Full error:", err);

                if (!res.headersSent) {
                    res.status(500).json({
                        error: "Detection processing failed",
                        details: err.message
                    });
                }

                // Still try to clean up the original uploaded file
                cleanup(imagePath);
            }
        });

        // Handle python process errors
        python.on('error', (err) => {
            console.error("❌ Python process error:", err);
            if (!res.headersSent) {
                res.status(500).json({
                    error: "Detection process failed to start",
                    details: err.message
                });
            }
        });

    } catch (error) {
        console.error("❌ Internal server error:", error);
        if (!res.headersSent) {
            res.status(500).json({ error: "Internal server error" });
        }
    }
};

// Helper function for cleanup
function cleanup(imagePath, resultDirPath = null) {
    // Clean up original uploaded image
    if (imagePath && fs.existsSync(imagePath)) {
        fs.unlink(imagePath, (err) => {
            if (err) {
                console.error("❌ Failed to delete original uploaded image:", err);
            } else {
                console.log("🧹 Deleted original uploaded image:", imagePath);
            }
        });
    }

    // Clean up result directory
    if (resultDirPath && fs.existsSync(resultDirPath)) {
        fs.rm(resultDirPath, { recursive: true, force: true }, (err) => {
            if (err) {
                console.error("❌ Failed to delete detection result folder:", err);
            } else {
                console.log("🧹 Deleted detection folder:", resultDirPath);
            }
        });
    }
}
