import mongoose from 'mongoose';

const MONGO_URI = process.env.MONGO_URI;

let cached = global.mongoose;
if (!cached) cached = global.mongoose = { conn: null, promise: null };

async function connectToDatabase() {
    if (!MONGO_URI) {
        throw new Error('MONGO_URI environment variable not set');
    }
    if (cached.conn) return cached.conn;
    if (!cached.promise) {
        cached.promise = mongoose.connect(MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true }).then(m => m);
    }
    cached.conn = await cached.promise;
    return cached.conn;
}

const userSchema = new mongoose.Schema({
    name: String,
    email: String,
    age: Number
});

const User = mongoose.models.User || mongoose.model('User', userSchema);

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' });

    try {
        await connectToDatabase();
    } catch (err) {
        return res.status(500).json({ message: 'Database connection error', error: err.message });
    }

    let email, name;
    try {
        ({ email, name } = req.body || {});
    } catch (err) {
        return res.status(400).json({ message: 'Invalid request body' });
    }

    if (!email || !name) {
        return res.status(400).json({ message: 'Name and email are required' });
    }

    try {
        const user = await User.findOne({ email, name });
        if (user) {
            res.status(200).json({ message: 'Login successful!' });
        } else {
            res.status(401).json({ message: 'Invalid credentials' });
        }
    } catch (err) {
        res.status(500).json({ message: 'Error during login', error: err.message });
    }
}
