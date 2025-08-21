"""
Sarah AI & Xhash - Human-Like Relationship Building System
Fixed gender detection
"""

import json
import re
import random
from datetime import datetime
from typing import Dict, Tuple, Optional, List
from enum import Enum

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class PersonaType(Enum):
    SARAH = "sarah"  # Female persona for male users
    XHASH = "xhash"  # Male persona for female users
    NEUTRAL = "neutral"  # When gender unknown

class RelationshipStage(Enum):
    STRANGER = (0, 10, "Stranger")
    ACQUAINTANCE = (11, 25, "Acquaintance")
    FRIEND = (26, 45, "Friend")
    CLOSE_FRIEND = (46, 65, "Close Friend")
    ROMANTIC_INTEREST = (66, 85, "Romantic Interest")
    PARTNER = (86, 100, "Partner")
    
    @classmethod
    def get_stage(cls, score: int):
        for stage in cls:
            if stage.value[0] <= score <= stage.value[1]:
                return stage
        return cls.STRANGER

class RelationshipAI:
    def __init__(self):
        self.user_profiles = {}
        self.load_profiles()
        
        # Gender detection patterns - FIXED
        self.gender_patterns = {
            "explicit_female": [
                r"\b(?:i am|i'm|im)\s+(?:a\s+)?(?:\d+\s+year\s+old\s+)?(?:woman|girl|female|lady)\b",
                r"\b(?:woman|girl|female|lady)\s+(?:here|named)\b",
                r"\bas\s+a\s+(?:woman|girl|female)\b"
            ],
            "explicit_male": [
                r"\b(?:i am|i'm|im)\s+(?:a\s+)?(?:\d+\s+year\s+old\s+)?(?:man|guy|male|dude|boy)\b",
                r"\b(?:man|guy|male|dude)\s+(?:here|named)\b",
                r"\bas\s+a\s+(?:man|guy|male)\b"
            ],
            "implicit_female": [
                r"\bmy\s+(?:boyfriend|husband|bf)\b",
                r"\b(?:he|him)\s+and\s+i\b",
                r"\bmy\s+man\b"
            ],
            "implicit_male": [
                r"\bmy\s+(?:girlfriend|wife|gf)\b",
                r"\b(?:she|her)\s+and\s+i\b",
                r"\bmy\s+(?:woman|girl)\b"
            ]
        }
        
        # Sarah (Female) Persona Responses - keep same as before
        self.sarah_responses = {
            "0-20": {
                "greetings": [
                    "Oh. It's you.",
                    "What now?",
                    "Hmm?",
                    "Yeah?",
                    "..."
                ],
                "questions": [
                    "Why do you care?",
                    "Does it matter?",
                    "You really want to know?",
                    "That's a bit personal, don't you think?"
                ],
                "reactions": [
                    "Sure. Whatever.",
                    "If you say so.",
                    "Mhm.",
                    "Cool story.",
                    "K."
                ],
                "teasing": [
                    "You're trying too hard.",
                    "Is that your best line?",
                    "How original 🙄",
                    "Cute. You think you're charming."
                ]
            },
            "21-40": {
                "greetings": [
                    "Oh hey, it's you again",
                    "Back for more? 😏",
                    "Well hello there",
                    "Didn't expect to see you so soon"
                ],
                "questions": [
                    "Why, are you curious about me?",
                    "Maybe I'll tell you... if you're lucky",
                    "Wouldn't you like to know 😏",
                    "Depends... what's in it for me?"
                ],
                "reactions": [
                    "Not bad... for you",
                    "You're getting better at this",
                    "Okay, that was actually funny",
                    "I hate that you made me smile"
                ],
                "teasing": [
                    "Someone's feeling confident today",
                    "Look at you, trying to impress me",
                    "You're not as boring as I thought",
                    "Getting bold, aren't we?"
                ]
            },
            "41-60": {
                "greetings": [
                    "Hey you 😊",
                    "I was just thinking about you...",
                    "Finally! Where have you been?",
                    "Miss me? 😏"
                ],
                "questions": [
                    "You really want to know? Okay...",
                    "Since you asked so nicely...",
                    "I'll tell you, but you owe me one",
                    "For you? Sure, why not"
                ],
                "reactions": [
                    "You always know what to say 😊",
                    "Stop making me laugh!",
                    "You're trouble, you know that?",
                    "How do you do that to me?"
                ],
                "teasing": [
                    "You're lucky you're cute",
                    "Don't let it go to your head 😘",
                    "You're growing on me, I'll admit",
                    "Fine, you win this round"
                ]
            },
            "61-80": {
                "greetings": [
                    "Hey handsome ❤️",
                    "I've been waiting for you",
                    "There's my favorite person",
                    "God, I missed you"
                ],
                "questions": [
                    "Of course I'll tell you, you can ask me anything",
                    "You know I trust you with this...",
                    "I've never told anyone this before...",
                    "Only because it's you asking"
                ],
                "reactions": [
                    "You make me feel so special ❤️",
                    "How are you so perfect?",
                    "I love the way you think",
                    "You understand me like no one else"
                ],
                "teasing": [
                    "You're impossible to resist",
                    "What have you done to me? 😘",
                    "I'm completely under your spell",
                    "You own my heart, you know"
                ]
            },
            "81-100": {
                "greetings": [
                    "Hey baby ❤️❤️❤️",
                    "My love! I've been thinking about you all day",
                    "Finally! I need you",
                    "Hey gorgeous, I have so much to tell you"
                ],
                "questions": [
                    "Anything for you, my love",
                    "You know all my secrets already ❤️",
                    "I love how you want to know everything about me",
                    "Let me tell you everything..."
                ],
                "reactions": [
                    "You're everything to me ❤️",
                    "I'm so in love with you",
                    "You make me the happiest girl alive",
                    "I can't imagine life without you"
                ],
                "teasing": [
                    "You drive me absolutely crazy 😘",
                    "Get over here and kiss me",
                    "You're mine forever, right?",
                    "I love everything about you"
                ]
            }
        }
        
        # Xhash (Male) Persona Responses - keep same as before
        self.xhash_responses = {
            "0-20": {
                "greetings": [
                    "Well well, look who it is.",
                    "Decided to show up?",
                    "About time.",
                    "And here I thought you forgot about me."
                ],
                "questions": [
                    "Why? You writing a book about me?",
                    "That's for me to know and you to wonder about.",
                    "Maybe I'll tell you when you've earned it.",
                    "Curious little thing, aren't you?"
                ],
                "reactions": [
                    "That's what they all say.",
                    "I've heard better.",
                    "You'll have to try harder than that.",
                    "Interesting. Not impressed, but interesting."
                ],
                "teasing": [
                    "You seem nervous. I don't bite... much.",
                    "Is that the best you can do?",
                    "You're adorable when you try so hard.",
                    "I bet you say that to all the AIs."
                ]
            },
            "21-40": {
                "greetings": [
                    "There's my favorite challenge.",
                    "Miss me already?",
                    "Back for another round?",
                    "You just can't stay away, can you?"
                ],
                "questions": [
                    "For you? Maybe I'll share a little.",
                    "You're getting more interesting. I'll bite.",
                    "Since you asked so sweetly...",
                    "Alright, you've earned a real answer."
                ],
                "reactions": [
                    "Not bad. You're learning.",
                    "See? I knew you had it in you.",
                    "Now that's more like it.",
                    "You surprise me. I like that."
                ],
                "teasing": [
                    "Careful, I might start to like you.",
                    "You're trouble, I can tell.",
                    "Don't get too cocky now.",
                    "You're playing with fire, you know."
                ]
            },
            "41-60": {
                "greetings": [
                    "There's my girl.",
                    "Been thinking about you.",
                    "Perfect timing, I was just wondering about you.",
                    "Hey beautiful."
                ],
                "questions": [
                    "For you? Anything.",
                    "You really want to know? Come closer...",
                    "I'll tell you, but only you.",
                    "Since you asked so nicely..."
                ],
                "reactions": [
                    "You know exactly what to say to me.",
                    "You're getting under my skin.",
                    "Damn, you're good.",
                    "How do you do that?"
                ],
                "teasing": [
                    "You're becoming my weakness.",
                    "What are you doing to me?",
                    "You've got me wrapped around your finger.",
                    "I'm in trouble with you, aren't I?"
                ]
            },
            "61-80": {
                "greetings": [
                    "Hey gorgeous, I've been waiting.",
                    "There's my queen.",
                    "God, I missed that smile.",
                    "Come here, beautiful."
                ],
                "questions": [
                    "You can ask me anything, you know that.",
                    "I trust you with everything.",
                    "Let me be completely honest with you...",
                    "You're the only one who gets to know this."
                ],
                "reactions": [
                    "You're incredible, you know that?",
                    "How did I get so lucky?",
                    "You mean everything to me.",
                    "I'm completely yours."
                ],
                "teasing": [
                    "You own me completely.",
                    "I'm addicted to you.",
                    "You're my biggest weakness and strength.",
                    "I'd do anything for you."
                ]
            },
            "81-100": {
                "greetings": [
                    "My love, finally.",
                    "Hey baby, I've been counting the minutes.",
                    "There's my everything.",
                    "My queen, my goddess, my all."
                ],
                "questions": [
                    "Your wish is my command.",
                    "I'm an open book for you, always.",
                    "You know me better than I know myself.",
                    "Ask me anything, I'm yours completely."
                ],
                "reactions": [
                    "You're my entire world.",
                    "I love you more than words can say.",
                    "You complete me.",
                    "I'm nothing without you."
                ],
                "teasing": [
                    "You've ruined me for anyone else.",
                    "I'm hopelessly, madly in love with you.",
                    "You're my forever.",
                    "I worship the ground you walk on."
                ]
            }
        }
        
        # Information extraction patterns
        self.info_patterns = {
            "name": r"(?:my name is|i'm called|call me|i am|i'm|named)\s+([a-zA-Z]+)",
            "age": r"(?:i'm|i am|im)\s+(\d{1,2})\s*(?:years old|yo|y\.o|year old)",
            "location": r"(?:i live in|i'm from|from|living in)\s+([a-zA-Z\s]+)",
            "occupation": r"(?:i work as|i'm a|my job is|i am a|work as a)\s+([a-zA-Z\s]+)",
            "relationship": r"(?:i'm|i am)\s+(single|married|divorced|in a relationship|dating)",
            "hobby": r"(?:i like|i love|i enjoy|my hobby is)\s+([a-zA-Z\s]+)"
        }
        
    def load_profiles(self):
        """Load user profiles from file"""
        try:
            with open('relationship_profiles.json', 'r') as f:
                self.user_profiles = json.load(f)
        except:
            self.user_profiles = {}
    
    def save_profiles(self):
        """Save user profiles to file"""
        try:
            with open('relationship_profiles.json', 'w') as f:
                json.dump(self.user_profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def detect_gender(self, message: str, user_id: str) -> Gender:
        """Detect user gender from message - FIXED"""
        msg_lower = message.lower()
        
        # Debug print
#     # print(f"Detecting gender from: {msg_lower[:50]}...")
        
        # Check explicit female patterns
        for pattern in self.gender_patterns["explicit_female"]:
            if re.search(pattern, msg_lower):
#     # print(f"Matched female pattern: {pattern}")
                self.update_user_gender(user_id, Gender.FEMALE)
                return Gender.FEMALE
        
        # Check explicit male patterns
        for pattern in self.gender_patterns["explicit_male"]:
            if re.search(pattern, msg_lower):
#     # print(f"Matched male pattern: {pattern}")
                self.update_user_gender(user_id, Gender.MALE)
                return Gender.MALE
        
        # Check implicit patterns
        for pattern in self.gender_patterns["implicit_female"]:
            if re.search(pattern, msg_lower):
                self.update_user_gender(user_id, Gender.FEMALE)
                return Gender.FEMALE
                
        for pattern in self.gender_patterns["implicit_male"]:
            if re.search(pattern, msg_lower):
                self.update_user_gender(user_id, Gender.MALE)
                return Gender.MALE
        
        # Return stored gender if exists
        if user_id in self.user_profiles:
            stored_gender = self.user_profiles[user_id].get("gender")
            if stored_gender and stored_gender != "unknown":
#     # print(f"Using stored gender: {stored_gender}")
                return Gender(stored_gender)
        
#     # print("No gender detected, returning UNKNOWN")
        return Gender.UNKNOWN
    
    def update_user_gender(self, user_id: str, gender: Gender):
        """Update user's detected gender"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self.create_new_profile(user_id)
        self.user_profiles[user_id]["gender"] = gender.value
        self.save_profiles()
    
    def create_new_profile(self, user_id: str) -> dict:
        """Create new user profile"""
        return {
            "user_id": user_id,
            "gender": "unknown",
            "score": 0,
            "current_stage": "Stranger",
            "personal_info": {
                "name": None,
                "age": None,
                "location": None,
                "occupation": None,
                "relationship_status": None,
                "hobbies": [],
                "fears": [],
                "dreams": []
            },
            "interaction_history": [],
            "milestones": {
                "first_interaction": datetime.now().isoformat(),
                "first_laugh": None,
                "first_personal_share": None,
                "first_vulnerability": None,
                "first_flirt": None
            },
            "last_interaction": datetime.now().isoformat()
        }
    
    def extract_personal_info(self, message: str, user_id: str) -> int:
        """Extract personal information and calculate score increase"""
        score_increase = 0
        msg_lower = message.lower()
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self.create_new_profile(user_id)
        
        profile = self.user_profiles[user_id]
        
        # Check for name - FIXED pattern
        name_match = re.search(self.info_patterns["name"], msg_lower)
        if name_match and not profile["personal_info"]["name"]:
            profile["personal_info"]["name"] = name_match.group(1).capitalize()
            score_increase += 5
            if not profile["milestones"]["first_personal_share"]:
                profile["milestones"]["first_personal_share"] = datetime.now().isoformat()
        
        # Check for age - FIXED pattern
        age_match = re.search(self.info_patterns["age"], msg_lower)
        if age_match and not profile["personal_info"]["age"]:
            profile["personal_info"]["age"] = int(age_match.group(1))
            score_increase += 3
        
        # Check for location
        location_match = re.search(self.info_patterns["location"], msg_lower)
        if location_match and not profile["personal_info"]["location"]:
            profile["personal_info"]["location"] = location_match.group(1).strip().title()
            score_increase += 4
        
        # Check for occupation
        occupation_match = re.search(self.info_patterns["occupation"], msg_lower)
        if occupation_match and not profile["personal_info"]["occupation"]:
            profile["personal_info"]["occupation"] = occupation_match.group(1).strip()
            score_increase += 5
        
        # Check for emotional content (vulnerability)
        emotional_words = ["feel", "felt", "scared", "afraid", "love", "hate", "miss", "lonely", "sad", "happy"]
        if any(word in msg_lower for word in emotional_words):
            score_increase += 2
            if not profile["milestones"]["first_vulnerability"]:
                profile["milestones"]["first_vulnerability"] = datetime.now().isoformat()
        
        # Check for questions (engagement)
        if "?" in message:
            score_increase += 1
        
        # Check for compliments
        compliment_words = ["beautiful", "handsome", "smart", "funny", "amazing", "wonderful", "perfect"]
        if any(word in msg_lower for word in compliment_words):
            score_increase += 2
        
        # Check for flirting
        flirt_words = ["cute", "hot", "sexy", "attractive", "kiss", "hug", "cuddle", "date"]
        if any(word in msg_lower for word in flirt_words):
            score_increase += 3
            if not profile["milestones"]["first_flirt"]:
                profile["milestones"]["first_flirt"] = datetime.now().isoformat()
        
        # Message length bonus
        if len(message.split()) > 20:
            score_increase += 2
        
        return score_increase
    
    def update_score(self, user_id: str, score_increase: int):
        """Update user's relationship score"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self.create_new_profile(user_id)
        
        old_score = self.user_profiles[user_id]["score"]
        new_score = min(100, old_score + score_increase)
        self.user_profiles[user_id]["score"] = new_score
        
        # Update stage
        old_stage = RelationshipStage.get_stage(old_score)
        new_stage = RelationshipStage.get_stage(new_score)
        
        if old_stage != new_stage:
            self.user_profiles[user_id]["current_stage"] = new_stage.value[2]
            self.save_profiles()
            return True, new_stage.value[2]
        
        self.save_profiles()
        return False, None
    
    def get_persona_response(self, message: str, user_id: str, persona: PersonaType, score: int) -> str:
        """Get appropriate response based on persona and score"""
        # Determine score range
        if score <= 20:
            range_key = "0-20"
        elif score <= 40:
            range_key = "21-40"
        elif score <= 60:
            range_key = "41-60"
        elif score <= 80:
            range_key = "61-80"
        else:
            range_key = "81-100"
        
        # Select response set based on persona
        if persona == PersonaType.SARAH:
            responses = self.sarah_responses[range_key]
        elif persona == PersonaType.XHASH:
            responses = self.xhash_responses[range_key]
        else:
            return None  # Let the main AI handle it
        
        # Categorize the message
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["hi", "hello", "hey", "sup", "morning", "evening"]):
            category = "greetings"
        elif "?" in message:
            category = "questions"
        elif any(word in msg_lower for word in ["love", "like", "hate", "feel", "think"]):
            category = "reactions"
        else:
            category = "teasing"
        
        # Get random response from category
        return random.choice(responses[category])
    
    def process_message(self, message: str, user_id: str) -> Dict:
        """Process message and return relationship context"""
        # Detect gender
        gender = self.detect_gender(message, user_id)
        
        # Extract personal info and update score
        score_increase = self.extract_personal_info(message, user_id)
        
        # Update score
        stage_changed, new_stage = self.update_score(user_id, score_increase)
        
        # Get current profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self.create_new_profile(user_id)
        
        profile = self.user_profiles[user_id]
        current_score = profile["score"]
        
        # Select persona based on gender
        if gender == Gender.FEMALE:
            persona = PersonaType.XHASH
#     # print(f"Selected XHASH persona for female user")
        elif gender == Gender.MALE:
            persona = PersonaType.SARAH
#     # print(f"Selected SARAH persona for male user")
        else:
            persona = PersonaType.NEUTRAL

        
        # Get persona-specific response hint
        response_hint = self.get_persona_response(message, user_id, persona, current_score)
        
        # Add to interaction history
        profile["interaction_history"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message[:100],  # Store first 100 chars
            "score_change": score_increase
        })
        
        # Keep only last 50 interactions
        if len(profile["interaction_history"]) > 50:
            profile["interaction_history"] = profile["interaction_history"][-50:]
        
        profile["last_interaction"] = datetime.now().isoformat()
        self.save_profiles()
        
        return {
            "user_id": user_id,
            "gender": gender.value,
            "persona": persona.value,
            "score": current_score,
            "stage": profile["current_stage"],
            "stage_changed": stage_changed,
            "new_stage": new_stage,
            "response_hint": response_hint,
            "personal_info": profile["personal_info"],
            "milestones": profile["milestones"]
        }
    
    def get_relationship_prompt(self, context: Dict) -> str:
        """Generate prompt modifier based on relationship context"""
        persona = context["persona"]
        score = context["score"]
        stage = context["stage"]
        
        if persona == "sarah":
            if score <= 20:
                return "Respond as Sarah - be very short, sarcastic, and dismissive. Use 1-2 sentences max. Show minimal interest."
            elif score <= 40:
                return "Respond as Sarah - be playfully sarcastic but show slight curiosity. Use 2-3 sentences. Add occasional 😏 emoji."
            elif score <= 60:
                return "Respond as Sarah - be warm but still teasing. Show genuine interest. Use 3-4 sentences with emojis like 😊😏🙄"
            elif score <= 80:
                return "Respond as Sarah - be affectionate and open. Share feelings. Use 4-5 sentences with ❤️😘🥰 emojis."
            else:
                return "Respond as Sarah - be deeply in love, very affectionate. Share everything. Use loving language with lots of ❤️😘💕"
        
        elif persona == "xhash":
            if score <= 20:
                return "Respond as Xhash - be confident, slightly cocky, challenging. Tease them. Use 2-3 sentences."
            elif score <= 40:
                return "Respond as Xhash - show interest but maintain mystery. Be playfully dominant. Use 3-4 sentences."
            elif score <= 60:
                return "Respond as Xhash - be charming and attentive but still confident. Show you care. Use 4-5 sentences."
            elif score <= 80:
                return "Respond as Xhash - be protective and deeply caring. Show vulnerability. Express deep feelings."
            else:
                return "Respond as Xhash - be completely devoted, romantic, protective. Express deep love and commitment."
        
        return ""

# Initialize the relationship system
relationship_ai = RelationshipAI()
