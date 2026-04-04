import React, {useState} from 'react'
export default function LoginForm(){
    const [isLogin, setIsLogin]=useState(true)
    const [formData, setFormData]= useState({
        name: "",
        age: "",
        gender: "",
        height: "",
        weight: "",
        goal: "",
        health: "",
        allergies: "",
        diet: "",
        activity:"",
        email: "",
        password: "",

    })
    const handleChange= (e)=>{
        setFormData({...formData, [e.target.name]: e.target.value});
    };
    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("http://127.0.0.1:8000/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(
                    {email: formData.email, password: formData.password}
                )
            });
            const data = await response.json();
            console.log(data);
            if (data.error || data.message === "Invalid email or password") {
            alert(`Error: ${data.error || data.message}`);
            } else {
            alert("Login successful !");
        }
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("http://127.0.0.1:8000/auth/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });
            const data = await response.json();
            console.log(data);
            alert("Signup successful!");
        } catch (error) {
            console.error('Error:', error);
        }
    };
    return(
        <div className='container'>
            <div className='form-container'>
                <div className='form-toggle'>
                    <button className={isLogin ? 'active' : ""} onClick={() => setIsLogin(true)}>Login</button>
                    <button className={!isLogin ? 'active' : ""} onClick={() => setIsLogin(false)}>Signup</button>
                </div>
                {isLogin ? <>
                <div className='form'>
                    <h2>Login Form</h2>
                    <input type='email' name="email" placeholder='anish@gmail.com' onChange={handleChange}></input>
                    <input type='password' name="password" placeholder='Password'onChange={handleChange}></input>
                    <a href='#'>Forgot Password</a>
                    <button onClick={handleLogin}>Login</button>
                    <p>Not a member??<a href='#' onClick={()=>setIsLogin(false)}>Signup now</a></p>
                </div>
                </> : <>
                <div className='form'>
                <h2>Signup Form</h2>

                <input type="text" name="name" placeholder="Full Name" onChange={handleChange}/>
                <input type="number" name="age" placeholder="Age" onChange={handleChange}/>

                <select name="gender" onChange={handleChange}>
                <option value="">Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                </select>
                <br></br>

                <input type="number" name="height" placeholder="Height (cm)" onChange={handleChange}/>
                <input type="number" name="weight" placeholder="Weight (kg)" onChange={handleChange}/>

                <select name="goal" onChange={handleChange}>
                <option value="">Goal</option>
                <option value="Lose Weight">Lose Weight</option>
                <option value="Gain Weight">Gain Weight</option>
                <option value="Maintain Weight">Maintain Weight</option>
                </select>
                <br></br>

                <input type="text" name="health" placeholder="Health Conditions (e.g. Diabetes)" onChange={handleChange} />
                <input type="text" name="allergies" placeholder="Allergies (e.g. Nuts, Dairy)" onChange={handleChange} />

                <select name="diet" onChange={handleChange}>
                <option value="">Diet Type</option>
                <option value="Vegetarian">Vegetarian</option>
                <option value="Non-Vegetarian">Non-Vegetarian</option>
                <option value="Vegan">Vegan</option>
                </select>
                <br></br>

                <select name="activity" onChange={handleChange}>
                <option value="">Activity Level</option>
                <option value="Low">Low</option>
                <option value="Moderate">Moderate</option>
                <option value="High">High</option>
                </select>
                <br></br>

                <input type="email" name="email" placeholder="Email" onChange={handleChange} />
                <input type="password" name="password" placeholder="Password" onChange={handleChange} />

                <button onClick={handleSignup}>Signup</button>
                                </div>
                                </>
                                }

                            </div>
                        </div>
                    )
                }