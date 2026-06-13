#!/usr/bin/env node
/**
 * Terminal test for AI Doctor doctor recommendations.
 * Run on VPS (has DB access): node scripts/test-ai-doctor-recommendations.js
 */
import { fetchRecommendedDoctors, appendDoctorRecommendations, stripInventedDoctorNames } from '../src/services/aiDoctorDoctors.js';
import { generateChatReply, checkBotHealth } from '../src/services/aiDoctorService.js';

const CITY = process.env.TEST_CITY || 'lahore';

function assert(condition, message) {
  if (!condition) {
    console.error('FAIL:', message);
    process.exit(1);
  }
}

console.log('==> AI Doctor recommendation tests');
console.log('    City:', CITY);

console.log('\n1) fetchRecommendedDoctors(neurologist, lahore) — should fallback to Lahore GPs');
const neuroLahore = await fetchRecommendedDoctors('neurologist', CITY);
console.log('   count:', neuroLahore.length);
neuroLahore.forEach((d) => console.log('   -', d.name, '|', d.specialty_name, '|', d.hospital_name));
assert(neuroLahore.length > 0, 'Expected at least one doctor for neurologist+lahore fallback');
assert(
  neuroLahore.some((d) => d.city_slug === CITY || d.hospital_name),
  'Expected doctors tied to Lahore'
);

console.log('\n2) stripInventedDoctorNames — removes fake Groq names');
const fakeGroq =
  'BestechCare has doctors.\n\nHere are a few names:\n\n1. Dr. Muhammad Ali (Neurologist)\n2. Dr. Saira Butt (Neurologist)\n\nBook on BestechCare.';
const stripped = stripInventedDoctorNames(fakeGroq);
console.log('   stripped:', stripped.replace(/\n/g, ' | '));
assert(!stripped.includes('Dr. Muhammad Ali'), 'Fake doctor name should be removed');
assert(stripped.includes('BestechCare has doctors'), 'Real text should remain');

console.log('\n3) appendDoctorRecommendations — adds real DB names');
const appended = appendDoctorRecommendations(stripped, neuroLahore, {
  language: 'en',
  specialtySlug: 'neurologist',
  citySlug: CITY,
});
console.log('   --- reply tail ---');
console.log(appended.split('\n').slice(-8).join('\n'));
assert(appended.includes(neuroLahore[0].name), 'Reply must include real doctor name from DB');

const health = await checkBotHealth(true);
if (!health.available) {
  console.log('\n4) generateChatReply — SKIPPED (Python bot not running locally)');
  console.log('\nAll local DB/unit tests passed.');
  process.exit(0);
}

console.log('\n4) generateChatReply — full end-to-end via Python bot + DB');
const messages = [
  { role: 'user', content: 'i have headache' },
  { role: 'user', content: 'Can you tell me doctor names in Lahore' },
];
const result = await generateChatReply(messages, CITY);
console.log('   recommended_doctors:', result.recommended_doctors.length);
result.recommended_doctors.forEach((d) => console.log('   -', d.name, '|', d.specialty_name));
assert(result.recommended_doctors.length > 0, 'generateChatReply must return recommended_doctors');
assert(
  result.recommended_doctors.some((d) => result.reply.includes(d.name)),
  'Reply text must include real doctor name'
);
assert(!/Dr\.\sMuhammad Ali/i.test(result.reply), 'Reply must not contain hallucinated Groq names');

console.log('\nAll tests passed.');
