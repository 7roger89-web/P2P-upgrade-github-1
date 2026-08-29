// THIEN-HA 3D-02 Golden Character — minimum production architecture
// Uses Three.js primitives with texture/material approximation for xianxia cultivator

import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';

export const GOLDEN_CHARACTER_CONFIG = {
  identity: 'golden_cultivator_01',
  displayName: 'Golden Xianxia Cultivator',
  height: 1.78,
  scale: 1.0,
  palette: {
    robeWhite: 0xf5f5f0,
    robeJade: 0x1a3a2a,
    goldTrim: 0xc9a84c,
    hairDark: 0x1a1005,
    skinWarm: 0xe0c8b0,
    swordSteel: 0x8899aa,
    swordGold: 0xc9a84c,
  }
};

export class GoldenCultivator {
  constructor(scene, socketsEnabled = false) {
    this.scene = scene;
    this.socketsEnabled = socketsEnabled;
    this.root = new THREE.Group();
    this.root.name = 'GoldenCultivator_Root';
    this.attachments = {};
    this.animationState = { tick: 0 };

    // Build base body (simple geometric rig)
    this.buildBody();
    // Build hair
    this.buildHair();
    // Build robe
    this.buildRobe();
    // Build sword attachment
    this.buildSword();
    // Build belt/accessory
    this.buildBelt();
    // Build cloak (optional, visible by default)
    this.buildCloak();

    scene.add(this.root);
  }

  buildBody() {
    // Head
    const headGeo = new THREE.SphereGeometry(0.13, 12, 10);
    const headMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.skinWarm, roughness: 0.6, metalness: 0.1 });
    this.head = new THREE.Mesh(headGeo, headMat);
    this.head.position.y = 1.62;
    this.head.name = 'head_mesh';
    this.root.add(this.head);

    // Torso (slightly tapered cylinder)
    const torsoGeo = new THREE.CylinderGeometry(0.22, 0.26, 0.55, 10);
    const torsoMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.robeWhite, roughness: 0.8, metalness: 0.05 });
    this.torso = new THREE.Mesh(torsoGeo, torsoMat);
    this.torso.position.y = 1.12;
    this.torso.name = 'torso_mesh';
    this.root.add(this.torso);

    // Inner dark jade layer (visible at collar)
    const collarGeo = new THREE.TorusGeometry(0.24, 0.04, 6, 10);
    const collarMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.robeJade, roughness: 0.7, metalness: 0.2 });
    this.collar = new THREE.Mesh(collarGeo, collarMat);
    this.collar.position.y = 1.36;
    this.collar.rotation.x = Math.PI / 2;
    this.collar.name = 'collar_mesh';
    this.root.add(this.collar);

    // Legs (simple cylinders) — visible below robe bottom
    const legGeo = new THREE.CylinderGeometry(0.07, 0.09, 0.6, 8);
    const legMat = new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.9, metalness: 0.05 });
    const leftLeg = new THREE.Mesh(legGeo, legMat);
    leftLeg.position.set(-0.08, 0.3, 0);
    leftLeg.name = 'leg_l_mesh';
    this.root.add(leftLeg);
    const rightLeg = new THREE.Mesh(legGeo, legMat);
    rightLeg.position.set(0.08, 0.3, 0);
    rightLeg.name = 'leg_r_mesh';
    this.root.add(rightLeg);

    // Neck connector
    const neckGeo = new THREE.CylinderGeometry(0.055, 0.055, 0.08, 8);
    const neckMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.skinWarm, roughness: 0.6 });
    this.neck = new THREE.Mesh(neckGeo, neckMat);
    this.neck.position.y = 1.47;
    this.neck.name = 'neck_mesh';
    this.root.add(this.neck);

    // Define sockets as empty groups (for attachment tracking)
    const sockets = [
      { name: 'head', target: this.head },
      { name: 'torso', target: this.torso },
      { name: 'waist', target: this.torso }, // approximate
      { name: 'back_root', target: this.torso },
      { name: 'back_weapon', target: this.torso },
      { name: 'waist_weapon', target: this.torso },
      { name: 'neck', target: this.neck },
      { name: 'hand_primary', target: this.torso },
      { name: 'hand_secondary', target: this.torso },
    ];

    sockets.forEach(s => {
      const socketObj = new THREE.Group();
      socketObj.name = `socket_${s.name}`;
      if (s.name === 'head') socketObj.position.copy(this.head.position);
      else if (s.name === 'torso' || s.name === 'back_root' || s.name === 'back_weapon' || s.name === 'waist') socketObj.position.set(0, 1.2 + (s.name === 'back_root' ? 0.08 : 0), s.name === 'back_root' ? -0.1 : 0);
      else if (s.name === 'neck') socketObj.position.copy(this.neck.position);
      else if (s.name === 'waist_weapon') socketObj.position.set(-0.15, 0.8, 0);
      else if (s.name === 'hand_primary') socketObj.position.set(0.28, 1.15, 0.05);
      else if (s.name === 'hand_secondary') socketObj.position.set(-0.28, 1.15, 0.05);
      this.root.add(socketObj);
      this.attachments[s.name] = { socket: socketObj, currentAttachment: null };
    });
  }

  buildHair() {
    // Main hair body: large tapered cylinder / cone for topknot
    const hairMainGeo = new THREE.CylinderGeometry(0.08, 0.12, 0.35, 8);
    const hairMainMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.hairDark, roughness: 0.9, metalness: 0.1 });
    this.hairMain = new THREE.Mesh(hairMainGeo, hairMainMat);
    this.hairMain.position.set(0, 1.72, 0);
    this.hairMain.name = 'hair_main_mesh';
    this.root.add(this.hairMain);

    // Loose hair strands at sides
    const strandGeo = new THREE.CylinderGeometry(0.015, 0.02, 0.25, 5);
    const strandMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.hairDark, roughness: 0.9 });
    const strandL = new THREE.Mesh(strandGeo, strandMat);
    strandL.position.set(-0.09, 1.58, 0.05);
    strandL.rotation.z = 0.2;
    strandL.name = 'hair_strand_l';
    this.root.add(strandL);
    const strandR = new THREE.Mesh(strandGeo, strandMat);
    strandR.position.set(0.09, 1.58, 0.05);
    strandR.rotation.z = -0.2;
    strandR.name = 'hair_strand_r';
    this.root.add(strandR);
  }

  buildRobe() {
    // Primary robe body — wider cylinder with open front
    const robeGeo = new THREE.CylinderGeometry(0.28, 0.38, 0.85, 10, 1, true, 0, Math.PI + 0.4);
    const robeMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.robeWhite, roughness: 0.75, metalness: 0.05, side: THREE.DoubleSide });
    this.robeBody = new THREE.Mesh(robeGeo, robeMat);
    this.robeBody.position.y = 0.85;
    this.robeBody.rotation.y = Math.PI / 8; // slight twist for elegance
    this.robeBody.name = 'robe_body_mesh';
    this.root.add(this.robeBody);

    // Jade-green outer layer accents (shoulder/collar area)
    const shoulderGeo = new THREE.BoxGeometry(0.35, 0.15, 0.28);
    const shoulderMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.robeJade, roughness: 0.7, metalness: 0.2 });
    this.shoulderL = new THREE.Mesh(shoulderGeo, shoulderMat);
    this.shoulderL.position.set(-0.22, 1.35, 0);
    this.shoulderL.name = 'shoulder_l_mesh';
    this.root.add(this.shoulderL);
    this.shoulderR = new THREE.Mesh(shoulderGeo, shoulderMat);
    this.shoulderR.position.set(0.22, 1.35, 0);
    this.shoulderR.name = 'shoulder_r_mesh';
    this.root.add(this.shoulderR);

    // Gold trim band at robe bottom
    const trimGeo = new THREE.TorusGeometry(0.36, 0.03, 6, 12);
    const trimMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.goldTrim, roughness: 0.3, metalness: 0.6 });
    this.trimBand = new THREE.Mesh(trimGeo, trimMat);
    this.trimBand.position.y = 0.55;
    this.trimBand.rotation.x = Math.PI / 2;
    this.trimBand.name = 'trim_band_mesh';
    this.root.add(this.trimBand);
  }

  buildSword() {
    // Sword handle + blade geometric approximation
    const bladeGeo = new THREE.BoxGeometry(0.02, 0.7, 0.06);
    const bladeMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.swordSteel, roughness: 0.3, metalness: 0.7 });
    this.swordBlade = new THREE.Mesh(bladeGeo, bladeMat);
    this.swordBlade.position.set(-0.14, 0.95, -0.08);
    this.swordBlade.rotation.z = -Math.PI / 12;
    this.swordBlade.name = 'sword_blade_mesh';
    this.root.add(this.swordBlade);

    const hiltGeo = new THREE.BoxGeometry(0.04, 0.08, 0.04);
    const hiltMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.swordGold, roughness: 0.2, metalness: 0.6 });
    this.swordHilt = new THREE.Mesh(hiltGeo, hiltMat);
    this.swordHilt.position.set(-0.14, 1.25, -0.08);
    this.swordHilt.name = 'sword_hilt_mesh';
    this.root.add(this.swordHilt);
  }

  buildBelt() {
    const beltGeo = new THREE.TorusGeometry(0.25, 0.03, 6, 10);
    const beltMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.robeJade, roughness: 0.6, metalness: 0.3 });
    this.belt = new THREE.Mesh(beltGeo, beltMat);
    this.belt.position.y = 0.82;
    this.belt.rotation.x = Math.PI / 2;
    this.belt.name = 'belt_mesh';
    this.root.add(this.belt);

    // Pendant
    const pendantGeo = new THREE.OctahedronGeometry(0.035);
    const pendantMat = new THREE.MeshStandardMaterial({ color: GOLDEN_CHARACTER_CONFIG.palette.goldTrim, roughness: 0.2, metalness: 0.7 });
    this.pendant = new THREE.Mesh(pendantGeo, pendantMat);
    this.pendant.position.set(0.26, 0.82, 0.02);
    this.pendant.name = 'belt_pendant_mesh';
    this.root.add(this.pendant);
  }

  buildCloak() {
    const cloakGeo = new THREE.BoxGeometry(0.35, 0.5, 0.08);
    const cloakMat = new THREE.MeshStandardMaterial({ color: 0xe8e8e0, roughness: 0.9, metalness: 0.05, transparent: true, opacity: 0.85 });
    this.cloak = new THREE.Mesh(cloakGeo, cloakMat);
    this.cloak.position.set(0, 1.35, -0.12);
    this.cloak.name = 'cloak_mesh';
    this.root.add(this.cloak);
  }

  // Attachment methods
  attach(componentName, socketName, mesh) {
    const socketData = this.attachments[socketName];
    if (!socketData) {
      console.warn('Unknown socket:', socketName);
      return;
    }
    // Remove previous attachment
    if (socketData.currentAttachment) {
      socketData.socket.remove(socketData.currentAttachment);
    }
    // Position mesh at socket location, then parent to socket
    mesh.position.set(0, 0, 0);
    mesh.rotation.set(0, 0, 0);
    socketData.socket.add(mesh);
    socketData.currentAttachment = mesh;
  }

  detach(socketName) {
    const socketData = this.attachments[socketName];
    if (socketData && socketData.currentAttachment) {
      socketData.socket.remove(socketData.currentAttachment);
      socketData.currentAttachment = null;
    }
  }

  showSockets(show = true) {
    this.socketsEnabled = show;
    Object.values(this.attachments).forEach(data => {
      if (show) {
        // Visualize socket with a small wireframe box
        const vis = new THREE.Mesh(
          new THREE.BoxGeometry(0.08, 0.08, 0.08),
          new THREE.MeshBasicMaterial({ color: 0xff0000, wireframe: true, transparent: true, opacity: 0.5 })
        );
        vis.name = `socket_vis_${data.socket.name}`;
        data.socket.add(vis);
      } else {
        const child = data.socket.children.find(c => c.name && c.name.includes('socket_vis'));
        if (child) data.socket.remove(child);
      }
    });
  }

  update(delta = 0.016) {
    this.animationState.tick += delta;
    // Gentle idle rotation + breathing
    this.root.rotation.y = Math.sin(this.animationState.tick) * 0.02;
    // Subtle vertical breathing on head and torso
    const breath = Math.sin(this.animationState.tick * 2) * 0.005;
    if (this.head) this.head.position.y = 1.62 + breath;
    if (this.torso) this.torso.position.y = 1.12 + breath * 0.5;
  }

  getRoot() { return this.root; }
}
