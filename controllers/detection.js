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
                console.log(`🐍 Python process exited with code: ${code}`);
                
                // Wait a bit for YOLOv8 to finish writing files
                await new Promise(resolve => setTimeout(resolve, 2000));

                // Try to find where YOLOv8 actually saved the results
                let detectPath = null;
                let resultDirPath = null;
                let resultImgPath = null;

                // Search in multiple possible locations
                const searchPaths = [
                    path.resolve(process.cwd(), 'runs', 'detect'),
                    path.resolve(__dirname, '..', 'runs', 'detect'),
                    path.resolve(__dirname, '..', '..', 'runs', 'detect'),
                    path.resolve('./runs/detect'),
                    path.resolve('./yolov8/runs/detect'),
                    path.resolve(process.cwd(), 'yolov8', 'runs', 'detect'),
                    // เพิ่มเส้นทางใหม่
                    path.resolve('/tmp/runs/detect'),
                    path.resolve(process.env.HOME || '/tmp', 'runs', 'detect')
                ];

                console.log("🔍 Searching for detection results in multiple paths...");
                
                for (const searchPath of searchPaths) {
                    console.log(`📁 Checking: ${searchPath}`);
                    
                    if (fs.existsSync(searchPath)) {
                        try {
                            const dirContents = fs.readdirSync(searchPath);
                            console.log(`📂 Contents of ${searchPath}:`, dirContents);
                            
                            const subDirs = dirContents
                                .map(name => ({
                                    name,
                                    fullPath: path.join(searchPath, name),
                                }))
                                .filter(entry => {
                                    try {
                                        return fs.statSync(entry.fullPath).isDirectory();
                                    } catch (err) {
                                        return false;
                                    }
                                })
                                .sort((a, b) => {
                                    try {
                                        return fs.statSync(b.fullPath).mtimeMs - fs.statSync(a.fullPath).mtimeMs;
                                    } catch (err) {
                                        return 0;
                                    }
                                });

                            if (subDirs.length > 0) {
                                detectPath = searchPath;
                                resultDirPath = subDirs[0].fullPath;
                                console.log(`✅ Found detection results at: ${resultDirPath}`);
                                break;
                            }
                        } catch (err) {
                            console.warn(`⚠️ Error reading ${searchPath}:`, err.message);
                        }
                    }
                }

                // ถ้าไม่เจอโฟลเดอร์ ให้ลองหาไฟล์ผลลัพธ์โดยตรง
                if (!resultDirPath) {
                    console.log("🔍 No subdirectories found, searching for result files directly...");
                    
                    // ลองหาไฟล์ในโฟลเดอร์ที่มีอยู่
                    const directSearchPaths = [
                        ...searchPaths,
                        // เพิ่มเส้นทางที่อาจจะมีไฟล์โดยตรง
                        path.dirname(imagePath), // โฟลเดอร์เดียวกับรูปต้นฉบับ
                        path.resolve(process.cwd()),
                        path.resolve(__dirname, '..'),
                        '/tmp'
                    ];

                    for (const searchPath of directSearchPaths) {
                        if (fs.existsSync(searchPath)) {
                            try {
                                const files = fs.readdirSync(searchPath);
                                const imageFiles = files.filter(file => 
                                    /\.(jpg|jpeg|png|webp)$/i.test(file) && 
                                    file !== path.basename(imagePath) // ไม่เอารูปต้นฉบับ
                                );
                                
                                if (imageFiles.length > 0) {
                                    // หาไฟล์ที่สร้างล่าสุด
                                    const newestFile = imageFiles
                                        .map(file => ({
                                            name: file,
                                            fullPath: path.join(searchPath, file),
                                            mtime: fs.statSync(path.join(searchPath, file)).mtimeMs
                                        }))
                                        .sort((a, b) => b.mtime - a.mtime)[0];
                                    
                                    resultImgPath = newestFile.fullPath;
                                    console.log(`✅ Found result image directly: ${resultImgPath}`);
                                    break;
                                }
                            } catch (err) {
                                console.warn(`⚠️ Error searching ${searchPath}:`, err.message);
                            }
                        }
                    }
                }

                // ถ้าเจอโฟลเดอร์แล้ว ให้หาไฟล์รูปในโฟลเดอร์นั้น
                if (resultDirPath && !resultImgPath) {
                    const resultFiles = fs.readdirSync(resultDirPath).filter(file =>
                        /\.(jpg|jpeg|png|webp)$/i.test(file)
                    );

                    if (resultFiles.length === 0) {
                        const allFiles = fs.readdirSync(resultDirPath);
                        throw new Error(`No image files found in result folder ${resultDirPath}. Found files: ${allFiles.join(', ')}`);
                    }

                    resultImgPath = path.join(resultDirPath, resultFiles[0]);
                }

                // ถ้าไม่เจอไฟล์ผลลัพธ์เลย
                if (!resultImgPath) {
                    // ให้ดู output จาก Python เพื่อหาเส้นทางจริง
                    console.log("🐍 Python output:", output);
                    
                    throw new Error("No result image found. Python output: " + output.trim());
                }

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