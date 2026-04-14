import React, {useState} from 'react'
import { useNavigate } from "react-router-dom";
export default function LoginForm(){
    const [isLogin, setIsLogin]=useState(true)
     const navigate = useNavigate();   

    const handleSignup = () => {     
        navigate("/preferences");
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
                    <input type='email' placeholder='anish@gmail.com'></input>
                    <input type='password' placeholder='Password'></input>
                    <a href='#'>Forgot Password</a>
                    <button>Login</button>
                   <p>
                        Not a member??
                        <button onClick={() => setIsLogin(false)}>
                            Signup now
                        </button>
                        </p>
                </div>
                </> : <>
                <div className='form'>
                <h2>Signup Form</h2>

                <input type="text" placeholder="Full Name" />
                <input type="number" placeholder="Age" />

                <select>
                <option>Gender</option>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
                </select>
                <br></br>

                <input type="number" placeholder="Height (cm)" />
                <input type="number" placeholder="Weight (kg)" />

                <select>
                <option>Goal</option>
                <option>Lose Weight</option>
                <option>Gain Weight</option>
                <option>Maintain Weight</option>
                </select>
                <br></br>

                <input type="text" placeholder="Health Conditions (e.g. Diabetes)" />
                <input type="text" placeholder="Allergies (e.g. Nuts, Dairy)" />

                <select>
                <option>Diet Type</option>
                <option>Vegetarian</option>
                <option>Non-Vegetarian</option>
                <option>Vegan</option>
                </select>
                <br></br>

                <select>
                <option>Activity Level</option>
                <option>Low</option>
                <option>Moderate</option>
                <option>High</option>
                </select>
                <br></br>

                <input type="email" placeholder="Email" />
                <input type="password" placeholder="Password" />

                <button onClick={handleSignup}>Signup</button>
                                </div>
                                </>
                                }

                            </div>
                        </div>
                    )
                }